from django.urls import path
from . import views

urlpatterns = [
    path('books/', views.list_books),
    # path('books/create/', views.create_book),
    # path('books/<int:book_id>/', views.get_book),
    # path('books/update/<int:book_id>/', views.update_book),
    # path('books/delete/<int:book_id>/', views.delete_book),

    path('users/', views.list_users),
    # path('users/create/', views.create_user),
    # path('users/<int:user_id>/', views.get_user),
    # path('users/update/<int:user_id>/', views.update_user),
    # path('users/delete/<int:user_id>/', views.delete_user),

    # path('loans/', views.list_loans),
    # path('loans/borrow/', views.borrow_book),
    # path('loans/return/<int:loan_id>/', views.return_book),
]
