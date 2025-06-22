from django.shortcuts import render
from django.db import connection
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .mongo import reviews_collection

def dictfetchall(cursor):
    "Return all rows from a cursor as a list of dicts"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def generate_new_book_id(cursor):
    cursor.execute("SELECT book_id FROM books ORDER BY book_id DESC LIMIT 1")
    last = cursor.fetchone()
    if last:
        # Ambil angka setelah huruf, misalnya "B012" → 12
        last_num = int(last[0][1:])
        new_num = last_num + 1
    else:
        new_num = 1

    # Format ke "B001", "B002", ..., "B123"
    return f"B{new_num:03}"



def home_page(request):
    with connection.cursor() as cursor:
        # 1. Buku paling sering dipinjam
        cursor.execute("""
            SELECT b.*,borrow_count
            FROM books b
            JOIN (
                SELECT book_id, COUNT(*) AS borrow_count
                FROM transactions
                GROUP BY book_id
                ORDER BY borrow_count DESC
                LIMIT 3
            ) t ON b.book_id = t.book_id
        """)
        most_borrowed = dictfetchall(cursor)

        cursor.execute("""
            SELECT * FROM books LIMIT 4
        """)
        all_books = dictfetchall(cursor)

        # 3. Buku terbaru ditambahkan (by book_id DESC)
        cursor.execute("SELECT * FROM books ORDER BY book_id DESC LIMIT 3")
        newest_books = dictfetchall(cursor)

        # 5. Buku baru terbit
        cursor.execute("SELECT * FROM books ORDER BY year_published DESC LIMIT 3")
        newest_published = dictfetchall(cursor)

        # 6. Buku klasik
        cursor.execute("SELECT * FROM books ORDER BY year_published ASC LIMIT 3")
        classic_books = dictfetchall(cursor)

        # 8. Rekomendasi minggu ini (dipinjam dalam 7 hari terakhir)
        cursor.execute("""
            SELECT b.*, weekly_borrow
            FROM books b
            JOIN (
                SELECT book_id, COUNT(*) AS weekly_borrow
                FROM transactions
                WHERE borrow_date >= CURDATE() - INTERVAL 7 DAY
                GROUP BY book_id
                ORDER BY weekly_borrow DESC
                LIMIT 3
            ) t ON b.book_id = t.book_id
        """)
        weekly_recommendation = dictfetchall(cursor)

    # 2. Buku rating tertinggi (MongoDB)
    top_rated = list(
        reviews_collection.aggregate([
            {"$group": {
                "_id": "$book_id",
                "avg_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1}
            }},
            {"$sort": {"avg_rating": -1}},
            {"$limit": 3}
        ])
    )
    # Ambil detail buku dari SQL berdasarkan book_id
    rated_books = []
    with connection.cursor() as cursor:
        for doc in top_rated:
            cursor.execute("SELECT * FROM books WHERE book_id = %s", [doc["_id"]])
            result = cursor.fetchone()
            if result:
                rated_books.append({
                    "book_id": result[0],
                    "title": result[1],
                    "author": result[2],
                    "publisher": result[3],
                    "year_published": result[4],
                    "image": result[5],
                    "available_copies": result[7],
                    "avg_rating": round(doc["avg_rating"],2),
                    "total_reviews": doc["review_count"]
                })

    # 7. Buku dengan review terbanyak
    most_reviewed_raw = list(
        reviews_collection.aggregate([
            {"$group": {
                "_id": "$book_id",
                "total_reviews": {"$sum": 1}
            }},
            {"$sort": {"total_reviews": -1}},
            {"$limit": 3}
        ])
    )
    most_reviewed = []
    with connection.cursor() as cursor:
        for doc in most_reviewed_raw:
            cursor.execute("SELECT * FROM books WHERE book_id = %s", [doc["_id"]])
            result = cursor.fetchone()
            if result:
                most_reviewed.append({
                    "book_id": result[0],
                    "title": result[1],
                    "author": result[2],
                    "publisher": result[3],
                    "year_published": result[4],
                    "image": result[5],
                    "available_copies": result[7],
                    "total_reviews": doc["total_reviews"]
                })
    # 4. Top 1 rating per kategori
    with connection.cursor() as cursor:
        cursor.execute("SELECT category_id, category_name FROM categories")
        all_categories = dictfetchall(cursor)

    top_per_category = []

    for cat in all_categories:
        # Get all book_id for this category
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT book_id
                FROM book_categories
                WHERE category_id = %s
            """, [cat["category_id"]])
            book_ids = [row[0] for row in cursor.fetchall()]

        if not book_ids:
            continue

        # Find top rated book from these book_ids in MongoDB
        top_book = reviews_collection.aggregate([
            {"$match": {"book_id": {"$in": book_ids}}},
            {"$group": {
                "_id": "$book_id",
                "avg_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1}
            }},
            {"$sort": {"avg_rating": -1}},
            {"$limit": 1}
        ])
        top_book = list(top_book)
        if not top_book:
            continue

        top_book = top_book[0]
        top_id = top_book["_id"]

        # Get full detail of that book
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE book_id = %s", [top_id])
            result = cursor.fetchone()
            if result:
                top_per_category.append({
                    "book_id": result[0],
                    "title": result[1],
                    "author": result[2],
                    "publisher": result[3],
                    "year_published": result[4],
                    "image": result[5],
                    "avg_rating": round(top_book["avg_rating"], 2),
                    "review_count": top_book["review_count"],
                    "category": cat["category_name"]
                })


    return render(request, "book/index.html", {
        "all_books": all_books,
        "most_borrowed": most_borrowed,
        "rated_books": rated_books,
        "newest_books": newest_books,
        "top_per_category": top_per_category,
        "newest_published": newest_published,
        "classic_books": classic_books,
        "most_reviewed": most_reviewed,
        "weekly_recommendation": weekly_recommendation,
    })


def search_books(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        sql = """
            SELECT * FROM books
            WHERE LOWER(title) LIKE %s
               OR LOWER(author) LIKE %s
               OR LOWER(publisher) LIKE %s
        """
        like_pattern = f"%{query.lower()}%"
        with connection.cursor() as cursor:
            cursor.execute(sql, [like_pattern, like_pattern, like_pattern])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'book/book.html', {
        'query': query,
        'all_books': results
    })

def book_page(request):
    with connection.cursor() as cursor:
        # Semua buku
        cursor.execute("""
            SELECT * FROM books
        """)
        all_books = dictfetchall(cursor)

        
    return render(request, "book/book.html", {
        "all_books": all_books,
    })


def book_detail(request, book_id):
    with connection.cursor() as cursor:
        # cursor.execute("SELECT * FROM books WHERE book_id = %s", [book_id])
        cursor.execute("""
            SELECT 
                b.book_id, b.title, b.author, b.publisher, b.year_published, 
                b.image, b.total_copies, b.available_copies, 
                b.total_ratings, b.total_reviews,
                GROUP_CONCAT(c.category_name SEPARATOR ', ') AS categories
            FROM books b
            LEFT JOIN book_categories bc ON b.book_id = bc.book_id
            LEFT JOIN categories c ON bc.category_id = c.category_id
            WHERE b.book_id = %s
            GROUP BY b.book_id
        """, [book_id])
        book = cursor.fetchone()
        if book:
            avg_rating = book[8] / book[9] if book[9] > 0 else 0  
        
    return render(request, "book/detail.html", {
        "book": book,
        "avg_rating": avg_rating,
        "round_avg_rating": round(avg_rating) if avg_rating else 0,
        "reviews": list(reviews_collection.find({"book_id": book_id}).sort("created_at", -1))
    })


@require_http_methods(["POST"])
def add_review(request, book_id):
    # if request.method == "POST":
    rating = request.POST.get("rating")
    comment = request.POST.get("comment")

    if rating:
        with connection.cursor() as cursor:
            # Ambil data lama
            cursor.execute("SELECT total_ratings, total_reviews FROM books WHERE book_id = %s", [book_id])
            result = cursor.fetchone()
            if result:
                old_total_rating, old_total_reviews = result
                new_total_reviews = old_total_reviews + 1
                new_total_rating = old_total_rating + int(rating)

                cursor.execute("""
                    UPDATE books
                    SET total_ratings = %s, total_reviews = %s
                    WHERE book_id = %s
                    """, [new_total_rating, new_total_reviews, book_id])

                review = {
                    "book_id": book_id,
                    "rating": int(rating),
                    "comment": comment,
                    "created_at": datetime.datetime.utcnow()
                }
                reviews_collection.insert_one(review)
    return redirect("book_detail", book_id=book_id)



# Dashboard opsional
def admin_dashboard(request):    
    with connection.cursor() as cursor:
        # Ambil data statistik atau informasi yang diperlukan untuk dashboard
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM members")
        total_members = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM transactions WHERE STATUS = 'borrowed'")
        active_borrows = cursor.fetchone()[0]

        cursor.execute("""
                SELECT 
                    transactions.*, 
                    members.name AS member_name, 
                    books.title AS book_title
                FROM transactions
                JOIN members ON transactions.member_id = members.member_id
                JOIN books ON transactions.book_id = books.book_id
            """)
        borrowed_books = cursor.fetchall()


    return render(request, "admin/dashboard.html",{
        "total_books": total_books,
        "total_members": total_members,
        "active_borrows": active_borrows,
        "borrowed_books": borrowed_books
    })

# Buku
def admin_book_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                b.book_id, b.title, b.author, b.publisher, b.year_published, 
                b.image, b.total_copies, b.available_copies, 
                b.total_ratings, b.total_reviews,
                GROUP_CONCAT(c.category_name SEPARATOR ', ') AS categories
            FROM books b
            LEFT JOIN book_categories bc ON b.book_id = bc.book_id
            LEFT JOIN categories c ON bc.category_id = c.category_id
            GROUP BY b.book_id
        """)
        books = cursor.fetchall()
    return render(request, "admin/book_list.html", {"books": books})

@require_http_methods(["POST", "GET"])
def admin_book_form(request, book_id=None):
    with connection.cursor() as cursor:
        # Ambil semua kategori untuk pilihan checkbox
        cursor.execute("SELECT category_id, category_name FROM categories")
        all_categories = cursor.fetchall()

        if request.method == "GET":
            if book_id:
                # Ambil data buku
                cursor.execute("SELECT * FROM books WHERE book_id = %s", [book_id])
                book = cursor.fetchone()

                # Ambil kategori terkait
                cursor.execute("SELECT category_id FROM book_categories WHERE book_id = %s", [book_id])
                book_categories = [row[0] for row in cursor.fetchall()]
            else:
                book = None
                book_categories = []

            return render(request, "admin/book_form.html", {
                "book": book,
                "all_categories": all_categories,
                "book_categories": book_categories
            })

        elif request.method == "POST":
            # Ambil data dari body request            
            title = request.POST["title"]
            author = request.POST["author"]
            publisher = request.POST["publisher"]
            year_published = request.POST["year"]
            image = request.POST.get("image") or 'https://tse3.mm.bing.net/th?id=OIP.TOmyV8UzAAggkG3oQRa6BgHaLH&pid=Api&P=0&h=180'
            total_copies = int(request.POST.get("stock", 0))
            available_copies = int(request.POST.get("available_copies", total_copies))
            category_ids = request.POST.getlist("categories")

            if book_id:  # UPDATE
                book_id_val = book_id
                cursor.execute("SELECT 1 FROM books WHERE book_id = %s", [book_id_val])
                if not cursor.fetchone():
                    return redirect("admin_book_list")

                cursor.execute("""
                    UPDATE books SET
                        title = %s, author = %s, publisher = %s,
                        year_published = %s, image = %s,
                        total_copies = %s, available_copies = %s
                    WHERE book_id = %s
                """, [title, author, publisher, year_published, image,
                      total_copies, available_copies, book_id_val])

                cursor.execute("DELETE FROM book_categories WHERE book_id = %s", [book_id_val])
            else:  # INSERT
                book_id_val = generate_new_book_id(cursor)
                cursor.execute("""
                    INSERT INTO books (book_id, title, author, publisher, year_published, image, total_copies, available_copies)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [book_id_val, title, author, publisher, year_published, image, total_copies, available_copies])

            # Insert kategori relasi
            for cat_id in category_ids:
                cursor.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", [book_id_val, cat_id])

            return redirect("admin_book_list")


@require_http_methods(["POST", "DELETE"])
def admin_book_delete(request, book_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM books WHERE book_id = %s", [book_id])
        if not cursor.fetchone():
            return redirect("admin_book_list")

        cursor.execute("DELETE FROM books WHERE book_id = %s", [book_id])
    return redirect("admin_book_list")


# Member
def admin_member_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM members")
        members = cursor.fetchall()
    return render(request, "admin/member_list.html", {
        "members": members
    })


@require_http_methods(["GET", "POST"])
def admin_member_form(request, member_id=None):
    member = None
    if member_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE member_id = %s", [member_id])
            row = cursor.fetchone()
            if row:
                member = {
                    'member_id': row[0],
                    'nama': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'address': row[4],
                    'role': row[5],
                }
            else:
                messages.error(request, "Member tidak ditemukan.")
                return redirect('admin_member_list')

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        role = request.POST.get('role', '').strip()

        errors = {}

        if not nama:
            errors['nama'] = 'Nama wajib diisi'
        if not email:
            errors['email'] = 'Email wajib diisi'
        if not phone:
            errors['phone'] = 'Nomor telepon wajib diisi'
        if not address:
            errors['address'] = 'Alamat wajib diisi'

        if not errors:
            with connection.cursor() as cursor:
                if member_id:
                    cursor.execute("""
                        UPDATE members SET name=%s, email=%s, phone=%s, address=%s, role=%s WHERE member_id=%s
                    """, [nama, email, phone, address, role, member_id])
                else:
                    cursor.execute("SELECT member_id FROM members ORDER BY member_id DESC LIMIT 1")
                    last_id_row = cursor.fetchone()
                    
                    if last_id_row:
                        last_id = last_id_row[0]  # contoh: 'M005'
                        last_num = int(last_id[1:])  # ambil angka setelah 'M'
                        new_id = f"M{last_num + 1:03}"  # tambahkan 1 dan format ke 3 digit, hasil: 'M006'
                    else:
                        new_id = "M001" 
                    cursor.execute("""
                        INSERT INTO members (member_id, name, email, phone, address, role) VALUES (%s,%s, %s, %s, %s, %s)
                    """, [new_id,nama, email, phone, address, role])
                messages.success(request, "Member berhasil disimpan.")                
            return redirect('admin_member_list')

        # Untuk render ulang form jika error
        context = {
            'errors': errors,
            'form_data': {
                'nama': nama,
                'email': email,
                'phone': phone,
                'address': address,
                'role': role,
            },
            'member': member,
        }
        return render(request, 'admin/member_form.html', context)

    return render(request, 'admin/member_form.html', {
        'member': member,
    })

@require_http_methods(["GET", "POST"])
def admin_member_delete(request, member_id):
    with connection.cursor() as cursor:
        # Cek apakah member ada dan ambil rolenya
        cursor.execute("SELECT role FROM members WHERE member_id = %s", [member_id])
        result = cursor.fetchone()

        if result is None:
            messages.error(request, "Member tidak ditemukan.")
        elif result[0] == 'admin':
            messages.error(request, "Tidak boleh menghapus member dengan role admin.")
        else:
            # Hapus member jika bukan admin
            cursor.execute("DELETE FROM members WHERE member_id = %s", [member_id])
            messages.success(request, "Member berhasil dihapus.")

    return redirect('admin_member_list')




@require_http_methods(["GET", "POST"])
def admin_loan_form(request, action, transaction_id=None):
    if request.method == "GET":
        # return action
        if action == "create":
            return render(request, "admin/loan_form.html", {"action": action})
        elif action == "return" and not transaction_id:
            # Jika tidak ada transaction_id, tampilkan daftar transaksi untuk dipilih
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT t.transaction_id, m.name AS member_name, b.title AS book_title, 
                           t.borrow_date, t.return_date, t.status, t.fine, t.status_fine
                    FROM transactions t
                    JOIN members m ON t.member_id = m.member_id
                    JOIN books b ON t.book_id = b.book_id
                    WHERE t.status IN ('returned', 'returned_late')
                """)
                transactions = cursor.fetchall()
            return render(request, "admin/borrow_list.html", {"transactions": transactions})
        elif action == "return" and transaction_id:
            # Ambil data transaksi untuk ditampilkan di form return
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", [transaction_id])
                transaction = cursor.fetchone()
                if not transaction:
                    return HttpResponseBadRequest("Transaksi tidak ditemukan.")
                return render(request, "admin/loan_form.html", {"transaction": transaction, "action": action})
        else:
            return redirect("admin_loan_form", action="create")  

    else:
        if action == "create":
            member_id = request.POST.get("member_id")
            book_id = request.POST.get("book_id")
            borrow_date = timezone.now().date()
            due_date = borrow_date + timezone.timedelta(days=7)
            if not member_id or not book_id:
                context = {
                    "error": "Member ID dan Book ID harus diisi.",
                    "action": action
                }
                return render(request, "admin/loan_form.html", context)

            # Cek apakah member dan buku ada di tabel
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM members WHERE member_id = %s", [member_id])
                if not cursor.fetchone():
                    context = {
                        "error": "Member tidak ditemukan.",
                        "action": action
                    }
                    return render(request, "admin/loan_form.html", context)

                cursor.execute("SELECT 1 FROM books WHERE book_id = %s AND available_copies > 0", [book_id])
                if not cursor.fetchone():
                    context = {
                        "error": "Buku tidak ditemukan atau tidak tersedia.",
                        "action": action
                    }
                    return render(request, "admin/loan_form.html", context)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO transactions (member_id, book_id, borrow_date, due_date)
                    VALUES (%s, %s, %s, %s)
                """, [member_id, book_id, borrow_date, due_date])

                # Update available_copies
                cursor.execute("""
                    UPDATE books
                    SET available_copies = available_copies - 1
                    WHERE book_id = %s AND available_copies > 0
                """, [book_id])

            return redirect("admin_dashboard")

        elif action == "return" and transaction_id:
            return_date = timezone.now().date()

            # Hitung denda (misal Rp1000 per hari keterlambatan)
            with connection.cursor() as cursor:
                cursor.execute("SELECT due_date FROM transactions WHERE transaction_id = %s", [transaction_id])
                row = cursor.fetchone()
                if not row:
                    return HttpResponseBadRequest("Transaksi tidak ditemukan.")

                due_date = row[0]
                days_late = (return_date - due_date).days
                fine = 0
                if days_late > 0:
                    fine = days_late * 5000

                status = 'returned_late' if fine > 0 else 'returned'
                status_fine = 'unpaid' if fine > 0 else 'paid'

                cursor.execute("""
                    UPDATE transactions
                    SET return_date = %s,
                        fine = %s,
                        status = %s,
                        status_fine = %s
                    WHERE transaction_id = %s
                """, [return_date, fine, status,status_fine, transaction_id])

                # Tambahkan kembali stok buku
                cursor.execute("""
                    UPDATE books
                    SET available_copies = available_copies + 1
                    WHERE book_id = (
                        SELECT book_id FROM transactions WHERE transaction_id = %s
                    )
                """, [transaction_id])

            return redirect("admin_loan_list",action="return")

        else:
            return HttpResponseBadRequest("Aksi tidak valid atau ID transaksi tidak diberikan.")