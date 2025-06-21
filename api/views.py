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
    books = execute_sql(f"""
            SELECT books.*, categories.category_name 
            FROM books 
            JOIN categories ON books.category_id = categories.category_id 
            WHERE books.book_id = {request.GET.get('book_id', '0')}
        """, fetch=True)
    # books = cursor.fetchone()
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


