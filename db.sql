CREATE DATABASE `fp_sbd_kel4`;
USE `fp_sbd_kel4`;

-- Tabel Kategori
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- Tabel Buku (Hapus kolom category_id karena akan digantikan oleh junction table)
CREATE TABLE books (
    book_id VARCHAR(10) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    year_published INT NOT NULL,
    image VARCHAR(255) DEFAULT 'https://tse3.mm.bing.net/th?id=OIP.TOmyV8UzAAggkG3oQRa6BgHaLH&pid=Api&P=0&h=180',
    total_copies INT DEFAULT 0,
    available_copies INT DEFAULT 0,
    total_ratings DECIMAL(13,2) DEFAULT 0.00,
    total_reviews INT DEFAULT 0
);

-- Tabel relasi buku ↔ kategori (many-to-many)
CREATE TABLE book_categories (
    book_id VARCHAR(10),
    category_id INT,
    PRIMARY KEY (book_id, category_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Tabel Member
CREATE TABLE members (
    member_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    registration_date DATE DEFAULT CURRENT_DATE,
    role ENUM('member', 'admin') DEFAULT 'member'
);

CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id VARCHAR(10),
    book_id VARCHAR(10),
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE DEFAULT NULL,
    fine DECIMAL(10, 2) DEFAULT 0.00,
    status ENUM('borrowed', 'returned', 'returned_late') DEFAULT 'borrowed',
    status_fine ENUM('paid', 'unpaid') DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(member_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

INSERT INTO categories (category_name) VALUES
('Fiksi'),
('Non-Fiksi'),
('Teknologi'),
('Sains'),
('Sejarah'),
('Biografi'),
('Psikologi'),
('Agama'),
('Komik'),
('Pendidikan');


INSERT INTO members (member_id, name, email, phone, address, role)
VALUES ('ADM001', 'Administrator', 'admin@library.com', '081234567890', 'Perpustakaan Pusat', 'admin');
