from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import connection

# Helper eksekusi SQL
def execute_sql(sql, params=(), fetch=False):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        if fetch:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return None

# Buku
def list_books(request):
    books = execute_sql("SELECT * FROM books", fetch=True)
    return JsonResponse(books, safe=False)

@csrf_exempt
def create_book(request):
    data = json.loads(request.body)
    execute_sql(
        "INSERT INTO books (title, author, stock) VALUES (?, ?, ?)",
        [data['title'], data['author'], data['stock']]
    )
    return JsonResponse({'message': 'Book created'})

# User
def list_users(request):
    users = execute_sql("SELECT * FROM members", fetch=True)
    return JsonResponse(users, safe=False)

@csrf_exempt
def create_user(request):
    data = json.loads(request.body)
    execute_sql(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        [data['name'], data['email']]
    )
    return JsonResponse({'message': 'User created'})

# Peminjaman
def list_loans(request):
    loans = execute_sql("""
        SELECT l.id, u.name, b.title, l.date_loaned, l.date_returned 
        FROM loans l 
        JOIN users u ON l.user_id = u.id 
        JOIN books b ON l.book_id = b.id
    """, fetch=True)
    return JsonResponse(loans, safe=False)

@csrf_exempt
def borrow_book(request):
    data = json.loads(request.body)
    execute_sql("""
        INSERT INTO loans (user_id, book_id, date_loaned) VALUES (?, ?, date('now'))
    """, [data['user_id'], data['book_id']])
    return JsonResponse({'message': 'Book borrowed'})

@csrf_exempt
def return_book(request, loan_id):
    execute_sql("UPDATE loans SET date_returned = date('now') WHERE id = ?", [loan_id])
    return JsonResponse({'message': 'Book returned'})
