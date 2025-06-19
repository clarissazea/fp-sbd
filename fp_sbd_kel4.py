import mysql.connector

# Koneksi ke database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="fp_sbd_kel4"
)

cursor = db.cursor()

def manajemen_buku():
    while True:
        print("\n=== Manajemen Buku ===")
        print("1. Lihat Daftar Buku")
        print("2. Tambah Buku")
        print("3. Update Buku")
        print("4. Hapus Buku")
        print("5. Kembali")

        pilihan = input("Pilih menu (1-5): ")

        if pilihan == "1":
            cursor.execute("SELECT * FROM books")
            hasil = cursor.fetchall()
            print("\n📚 Daftar Buku:")
            for buku in hasil:
                print(f"- [{buku[0]}] {buku[1]} oleh {buku[2]} | Kategori: {buku[5]} | Tersedia: {buku[7]}/{buku[6]}")
        
        elif pilihan == "2":
            book_id = input("Masukkan ID Buku: ")
            title = input("Masukkan Judul Buku: ")
            author = input("Masukkan Pengarang: ")
            publisher = input("Masukkan Penerbit: ")
            year_published = int(input("Masukkan Tahun Terbit: "))
            category = input("Masukkan Kategori: ")
            total_copies = int(input("Masukkan Total Salinan: "))
            available_copies = total_copies

            sql = """INSERT INTO books 
                (book_id, title, author, publisher, year_published, category, total_copies, available_copies) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (book_id, title, author, publisher, year_published, category, total_copies, available_copies)
            cursor.execute(sql, val)
            db.commit()
            print("Buku berhasil ditambahkan.")

        elif pilihan == "3":
            book_id = input("Masukkan ID Buku yang ingin di-update: ")
            cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
            data = cursor.fetchone()
            if data:
                print("Masukkan data baru (kosongkan jika tidak ingin mengubah):")
                title = input(f"Judul ({data[1]}): ") or data[1]
                author = input(f"Pengarang ({data[2]}): ") or data[2]
                publisher = input(f"Penerbit ({data[3]}): ") or data[3]
                year_published = input(f"Tahun Terbit ({data[4]}): ") or data[4]
                category = input(f"Kategori ({data[5]}): ") or data[5]
                total_copies = input(f"Total Salinan ({data[6]}): ") or data[6]
                available_copies = input(f"Salinan Tersedia ({data[7]}): ") or data[7]

                sql = """UPDATE books SET title=%s, author=%s, publisher=%s, 
                         year_published=%s, category=%s, total_copies=%s, available_copies=%s 
                         WHERE book_id=%s"""
                val = (title, author, publisher, int(year_published), category, int(total_copies), int(available_copies), book_id)
                cursor.execute(sql, val)
                db.commit()
                print("Buku berhasil diperbarui.")
            else:
                print("Buku tidak ditemukan.")

        elif pilihan == "4":
            book_id = input("Masukkan ID Buku yang ingin dihapus: ")
            cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
            if cursor.fetchone():
                konfirmasi = input(f"Yakin ingin menghapus buku dengan ID {book_id}? (y/n): ")
                if konfirmasi.lower() == 'y':
                    cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
                    db.commit()
                    print("Buku berhasil dihapus.")
                else:
                    print("Penghapusan dibatalkan.")
            else:
                print("Buku tidak ditemukan.")

        elif pilihan == "5":
            print("Kembali ke menu utama.")
            break
        else:
            print("Pilihan tidak valid. Silakan pilih antara 1-5.")


def tambah_anggota():
    member_id = input("Masukkan ID Anggota: ")
    name = input("Masukkan Nama: ")
    email = input("Masukkan Email: ")
    phone = input("Masukkan Nomor Telepon: ")
    address = input("Masukkan Alamat: ")
    registration_date = input("Masukkan Tanggal Registrasi (YYYY-MM-DD): ")

    sql = """INSERT INTO members 
        (member_id, name, email, phone, address, registration_date) 
        VALUES (%s, %s, %s, %s, %s, %s)"""
    val = (member_id, name, email, phone, address, registration_date)
    cursor.execute(sql, val)
    db.commit()
    print("Anggota berhasil ditambahkan.")

def peminjaman_buku():
    member_id = input("Masukkan ID Anggota: ")
    book_id = input("Masukkan ID Buku: ")
    borrow_date = input("Masukkan Tanggal Pinjam (YYYY-MM-DD): ")
    due_date = input("Masukkan Tanggal Jatuh Tempo (YYYY-MM-DD): ")

    sql = """INSERT INTO borrow_transactions 
        (member_id, book_id, borrow_date, due_date) 
        VALUES (%s, %s, %s, %s)"""
    val = (member_id, book_id, borrow_date, due_date)
    cursor.execute(sql, val)

    update_sql = """UPDATE books 
        SET available_copies = available_copies - 1 
        WHERE book_id = %s AND available_copies > 0"""
    cursor.execute(update_sql, (book_id,))

    db.commit()
    print("Transaksi peminjaman berhasil.")

def pengembalian_buku():
    transaction_id = int(input("Masukkan ID Transaksi Peminjaman: "))
    return_date = input("Masukkan Tanggal Kembali (YYYY-MM-DD): ")
    fine = float(input("Masukkan Denda (jika ada, 0 jika tidak): "))

    sql = """INSERT INTO return_transactions 
        (transaction_id, return_date, fine) 
        VALUES (%s, %s, %s)"""
    val = (transaction_id, return_date, fine)
    cursor.execute(sql, val)

    update_status_sql = """UPDATE borrow_transactions 
        SET status = 'returned' 
        WHERE transaction_id = %s"""
    cursor.execute(update_status_sql, (transaction_id,))

    get_book_sql = """SELECT book_id 
        FROM borrow_transactions 
        WHERE transaction_id = %s"""
    cursor.execute(get_book_sql, (transaction_id,))
    book = cursor.fetchone()

    if book:
        book_id = book[0]
        update_book_sql = """UPDATE books 
            SET available_copies = available_copies + 1 
            WHERE book_id = %s"""
        cursor.execute(update_book_sql, (book_id,))

    db.commit()
    print("Transaksi pengembalian berhasil.")

def menu():
    while True:
        print("\n=== MENU LIBRARY ===")
        print("1. Manajemen Buku")
        print("2. Tambah Anggota")
        print("3. Peminjaman Buku")
        print("4. Pengembalian Buku")
        print("0. Keluar")

        pilihan = input("Pilih menu: ")

        if pilihan == '1':
            manajemen_buku()
        elif pilihan == '2':
            tambah_anggota()
        elif pilihan == '3':
            peminjaman_buku()
        elif pilihan == '4':
            pengembalian_buku()
        elif pilihan == '0':
            print("Terima kasih telah menggunakan sistem library.")
            break
        else:
            print("Pilihan tidak valid, silakan coba lagi.")

menu()