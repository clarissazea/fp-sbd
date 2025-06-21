# from django.shortcuts import render

# def home_page(request):
#     return render(request, 'index.html')  

# def admin_page(request):
#     return render(request, 'admin/index.html')

# def book_page(request):
# return render(request, 'book/detail.html')

# def book_detail(request, book_id):
#     # Here you would typically fetch the book details from the database using the book_id
#     # For demonstration, we'll just return a placeholder response
#     context = {
#         'book_id': book_id,
#         'title': 'Sample Book Title',
#         'author': 'Sample Author',
#         'description': 'This is a sample description of the book.'
#     }
#     return render(request, 'book/detail.html', context)

from django.shortcuts import render
from django.db import connection
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone


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
        # Semua buku
        cursor.execute("SELECT * FROM books")
        all_books = cursor.fetchall()

        # Top 5 buku terpopuler
        # cursor.execute("""
        #     SELECT b.id, b.judul, COUNT(l.id) AS jumlah_pinjam
        #     FROM library_app_loan l
        #     JOIN library_app_book b ON l.book_id = b.id
        #     GROUP BY b.id
        #     ORDER BY jumlah_pinjam DESC
        #     LIMIT 5
        # """)
        # popular_books = cursor.fetchall()

        # Buku tahun terbit lama
        # cursor.execute("""
        #     SELECT * FROM library_app_book ORDER BY tahun ASC LIMIT 5
        # """)
        old_books = cursor.fetchall()

        # Buku terbaru
        # cursor.execute("""
        #     SELECT * FROM library_app_book ORDER BY tahun DESC LIMIT 5
        # """)
        # new_books = cursor.fetchall()

        # Top buku per kategori (1 buku per kategori sebagai contoh)
        # cursor.execute("""
        #     SELECT b1.id, b1.judul, b1.kategori FROM library_app_book b1
        #     WHERE b1.id IN (
        #         SELECT b2.id FROM library_app_book b2
        #         WHERE b2.kategori IS NOT NULL
        #         GROUP BY b2.kategori
        #         ORDER BY MAX(b2.tahun) DESC
        #     )
        #     LIMIT 5
        # """)
        # category_reco = cursor.fetchall()

    return render(request, "book/index.html", {
        "all_books": all_books,
        # "popular_books": popular_books,
        # "old_books": old_books,
        # "new_books": new_books,
        # "category_reco": category_reco
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
            avg_rating = book[7] // book[8] if book[8] > 0 else 0  
        
    return render(request, "book/detail.html", {
        "book": book,
        "avg_rating": avg_rating
    })

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