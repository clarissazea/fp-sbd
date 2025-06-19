# fp-sbd

# 1. Buat virtualenv & aktifkan
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows

# 2. Install Django
pip install django

# 3. Inisialisasi proyek dan app
django-admin startproject library .
python manage.py startapp api

# 4. Tambahkan 'api' ke settings.py > INSTALLED_APPS
# 5. Jalankan migrasi awal
python manage.py migrate

# 6. Jalankan server
python manage.py runserver
