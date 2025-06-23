"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from library.views import *

urlpatterns = [
    # path('admin/', admin.site.urls),
    # user
    # path('api/', include('api.urls')),

    # user
    path('', home_page, name='home_page'),
    path('book/', book_page, name='book_page'),
    path('book/search/', search_books, name='search_books'),
    path('book/<book_id>/', book_detail, name='book_detail'),
    path('book/review/<book_id>/', add_review, name='book_review'),
    

    # admin 
    path('admin/', admin_dashboard, name='admin_dashboard'),

     
    # Buku
    path('admin/books/', admin_book_list, name='admin_book_list'),
    path('admin/books/add/', admin_book_form, name='admin_book_form'),
    path('admin/books/edit/<book_id>/', admin_book_form, name='admin_book_edit'),
    path('admin/books/delete/<book_id>/', admin_book_delete, name='admin_book_delete'),

    # Member
    path('admin/members/', admin_member_list, name='admin_member_list'),
    path('admin/members/add/', admin_member_form, name='admin_member_form'),
    path('admin/members/edit/<member_id>/', admin_member_form, name='admin_member_edit'),
    path('admin/members/delete/<member_id>/', admin_member_delete, name='admin_member_delete'),

    # Peminjaman
    path('admin/borrow/<action>/', admin_loan_form, name='admin_loan_form'),
    path('admin/borrow/<action>/<transaction_id>/', admin_loan_form, name='admin_loan_return'),
    path('admin/borrow/<action>/', admin_loan_form, name='admin_loan_list'),

    path('admin/paid/<transaction_id>/', admin_paid_confirm, name='admin_fine_confirm'),
]
