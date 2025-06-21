# fp-sbd (LIBRARY MANAGEMENT)



## DEMO SETUP (RECOMENDED FOR LINUX)
#### 1. DATABASE
- Buat database, table dan isinya dari file .sql (mySQL)
- edit file `library/settings.py` kemudian bagian `[database]` edit sesuai kebutuhan database (kredensial dan nama database)

#### 2. DEPENDENCY
- install dependency yang dibutuhkan (ada pada file requirements.txt)
- atau run command `pip install -r requirements.txt` agar otomatis terinstall

#### 3. RUN
- run dengan command `python3 manage.py runserver`
- buka di browser `localhost:8000`




## SETUP FROM ZERO
#### 1. Buat virtualenv & aktifkan
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows

#### 2. Install Django
pip install django

#### 3. Inisialisasi proyek dan app
django-admin startproject library .
python manage.py startapp api

#### 4. Tambahkan 'api' ke settings.py > INSTALLED_APPS
#### 5. Jalankan migrasi awal
python manage.py migrate

#### 6. Jalankan server
python manage.py runserver
