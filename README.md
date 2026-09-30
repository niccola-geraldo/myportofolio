# myportofolio

Nama : Niccola Geraldo Winaryo Durand

NPM : 2506619070

Kelas : PBP F

Website portofolio pribadi dengan Django. Menampilkan profil dan bio, section Skills, section Projects, section Experience, serta section Education (dengan fitur form & data delivery).

## Cara Menjalankan

1. Aktifkan virtual environment:

   ```bash
   env\Scripts\activate
   ```

2. Instal dependensi (jika belum):

   ```bash
   pip install -r requirements.txt
   ```

3. Buat file `.env` di root project untuk development:
    ```dotenv
    PRODUCTION=False
    DEBUG=True
    DJANGO_SECRET_KEY=<secret-key-lokal>
    ```

   Buat secret key lokal yang acak dan jangan commit file environment. Untuk production, atur `PRODUCTION=True`, `DEBUG=False`, `DJANGO_SECRET_KEY`, dan variabel database di environment hosting. Karena settings memilih `.env.prod` berdasarkan nilai `PRODUCTION` yang tersedia sebelum Django dimulai, hosting harus menyediakan `PRODUCTION=True` secara langsung; jangan mengandalkan file `.env.prod` yang di-ignore Git.

4. Jalankan server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. Buka `http://127.0.0.1:8000/` di browser.

## Mengatur Editor

1. Login ke `/admin` menggunakan akun superuser.
2. Buat group dengan nama persis `Editor` pada bagian Groups.
3. Tambahkan pengguna yang diizinkan mengedit ke group tersebut.

Editor dapat mengubah Projects, Experience, dan Education, tetapi hanya superuser yang dapat menambah atau menghapus data.

## Refleksi
### Tugas 1

1. Struktur halaman tersusun dari `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, dan `<footer>`. Elemen semantik HTML5 akan membuat struktur website lebih terstruktur dan mudah untuk dibaca manusia maupun robot search engine.

2. Tantangan utama dari mengatur CSS website agar tetap responsive adalah ketika berhadapan dengan platform mobile atau layar kecil. Solusi dari tantangan ini adalah menggunakan fungsi clamp pada teks dan juga jarak antar section diperbesar.

3. Batasan yang saya alami ketika membuat web dengan gaya static web murni ini adalah semua konten harus ditulis secara manual dan *hardcoded* dalam konten HTML atau CSS itu sendiri. Saya juga tidak bisa membuat efek-efek visual yang memerlukan depedensi-dependensi lain dari elemen-elemen static web yang digunakan saat ini.

### Tugas 2

1. Alur MVT memisahkan tanggung jawab: `Project` (model) menyimpan data, `show_projects` (view) mengambil data dan memasukkannya ke context, lalu template `projects.html` merender data. Ini artinya data tidak di-*hardcode* di HTML, tetapi get dari database.

2. Perbedaan utama antara section Experience (Tutorial 02) dan Projects (Tugas 2) terletak pada tipe datanya: model `Experience` memiliki field tanggal (`started_at`, `ended_at`) serta properti `is_ongoing` untuk status, sedangkan model `Project` menyimpan `tech_stack` dan `link`. Pola MVT-nya tetap sama saja, tetapi field dan tampilannya yang disesuaikan.

3. Migrasi Django membuat perubahan model terstruktur dan mudah diterapkan. Kedua command tersebut memastikan struktur database selalu sinkron dengan definisi model tanpa perlu menulis SQL secara manual.

### Tugas 3

Pada tugas ini saya menambahkan section **Education** dengan mekanisme form & data delivery: model `Education` (institusi, jenjang, jurusan, tahun mulai/selesai, GPA), `EducationForm` (ModelForm), serta view `show_education`, `create_education`, `update_education`, `delete_education`, dan `get_education_json`. Halaman `education.html` menampilkan data hasil *fetch* endpoint JSON yang kemudian di-*deserialize*, dan form create/update dipakai bersama oleh satu template `education_form.html`. Seluruh halaman juga di-refactor agar melakukan *extend* terhadap `base.html` (termasuk blok `title`), dan endpoint JSON juga ditambahkan untuk Experience.

1. Saya menggunakan ModelForm karena form otomatis digenerate dari definisi model: jenis input, label, dan aturan validasi mengikuti field model sehingga kita tidak perlu menulis ulang HTML form dan logika validasi secara manual, dan setiap perubahan model langsung tercermin di form. `form.save()` juga langsung menyimpan instance ke database. Form HTML manual harus memvalidasi dan menyimpan tiap field sendiri sehingga rawan tidak sinkron dengan model. `{% csrf_token %}` wajib ditambahkan karena token rahasia unik per sesi ini menjadi bukti bahwa permintaan POST berasal dari form milik situs kita sendiri. Middleware `CsrfViewMiddleware` memvalidasi token tersebut sehingga serangan CSRF (penyerang memalsukan permintaan dari situs lain atas nama pengguna) tidak dapat terjadi, dan POST tanpa token akan ditolak dengan 403.

2. JSON dipakai karena lebih ringkas dan mudah dibaca.

3. Alurnya: view mengambil QuerySet dari database, lalu `serializers.serialize("json", queryset)` mengubah objek model Python menjadi string JSON berisi array objek `{model, pk, fields}`, dan `HttpResponse` mengirim string tersebut dengan header `Content-Type: application/json`. Serialization diperlukan karena HTTP hanya mengirim bytes, sedangkan objek model Python berisi tipe data dalam bentuk *human readable* (UUID, Decimal, DateTime) yang tidak bisa dikirim langsung.

### Tutorial 4

1. Autentikasi mengenali pengguna, sedangkan otorisasi menentukan tindakan yang boleh dilakukan. Menyembunyikan kontrol di template membantu antarmuka, tetapi pemeriksaan izin tetap harus dilakukan di view.

2. Django mempertahankan status login melalui session yang dikenali lewat cookie. Cookie `last_login` adalah informasi tambahan dan harus dibersihkan saat logout; form yang mengubah data tetap memerlukan perlindungan CSRF.

3. Relasi many-to-many cocok untuk star karena satu pengguna dapat memberi star pada banyak proyek dan satu proyek dapat menerima star dari banyak pengguna.

### Tutorial 5

Halaman Projects mengambil data secara asynchronous melalui Fetch API. Pencarian memakai debounce 300 ms dan pembatalan request sebelumnya agar hasil lama tidak menggantikan hasil terbaru. Penambahan proyek memakai modal dan endpoint JSON dengan validasi ModelForm serta CSRF. Kartu proyek dibuat dengan DOM API dan `textContent`, sementara URL gambar/tautan dibatasi ke HTTP(S), untuk menghindari XSS saat menampilkan data.

## AI Disclosure

Pengerjaan tugas ini dibantu oleh AI. 
Tool(s) yang digunakan: 
- **opencode**
- **DeepSeek Harness**

Model(s) yang digunakan:
- **deepseek-v4.1-flash**

Bagian yang dibantu:

- Menyusun model `Project`, view `show_projects`, routing `main:show_projects`, dan template `projects.html` mengikuti pola MVT section Experience.
- Menulis CSS untuk tata letak kartu section Projects agar konsisten dengan style yang ada.
- Membantu menyusun dan memformat README.
- Menyusun model `Education`, `EducationForm`, view create/update/delete/JSON, routing, dan template `education.html`/`education_form.html`.
- Menulis test baru untuk section Education, endpoint JSON, dan pencarian Projects.
- Meninjau konfigurasi secret key dan debug, menerapkan pemeriksaan akses owner untuk perubahan data, serta menambahkan test autentikasi, session, cookie, CSRF, dan star untuk Tutorial 4.
- Menerapkan peran Editor dan aturan akses untuk Projects, Experience, dan Education, termasuk form CRUD/pembaruan yang diperlukan serta pengujian otorisasi untuk Individual Assignment 4.

Perubahan yang dibantu AI telah diverifikasi dengan pengujian otomatis. Tinjauan akhir sebelum pengumpulan tetap menjadi tanggung jawab pemilik proyek.
