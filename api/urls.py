from django.urls import path
from . import views

urlpatterns = [
    path('books/', views.list_books),
    path('books/create/', views.create_book),
    path('users/', views.list_users),
    path('users/create/', views.create_user),
    path('loans/', views.list_loans),
    path('loans/borrow/', views.borrow_book),
    path('loans/return/<int:loan_id>/', views.return_book),
]
