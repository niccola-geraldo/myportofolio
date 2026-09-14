# myportofolio

Nama : Niccola Geraldo Winaryo Durand

NPM : 2506619070

Kelas : PBP F

Website portofolio pribadi dengan Django. Menampilkan profil dan bio, section Skills, serta section Projects.

## Cara Menjalankan

1. Aktifkan virtual environment:

   ```bash
   env\Scripts\activate
   ```

2. Instal dependensi (jika belum):

   ```bash
   pip install -r requirements.txt
   ```

3. Buat file .env di root project:
    ```bash
    PRODUCTION=False
    ```

4. Jalankan server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. Buka `http://127.0.0.1:8000/` di browser.

## Refleksi
### Tugas 1

1. Struktur halaman tersusun dari `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, dan `<footer>`. Elemen semantik HTML5 akan membuat struktur website lebih terstruktur dan mudah untuk dibaca manusia maupun robot search engine.

2. Tantangan utama dari mengatur CSS website agar tetap responsive adalah ketika berhadapan dengan platform mobile atau layar kecil. Solusi dari tantangan ini adalah menggunakan fungsi clamp pada teks dan juga jarak antar section diperbesar.

3. Batasan yang saya alami ketika membuat web dengan gaya static web murni ini adalah semua konten harus ditulis secara manual dan *hardcoded* dalam konten HTML atau CSS itu sendiri. Saya juga tidak bisa membuat efek-efek visual yang memerlukan depedensi-dependensi lain dari elemen-elemen static web yang digunakan saat ini.

### Tugas 2

1. Alur MVT memisahkan tanggung jawab: `Project` (model) menyimpan data, `show_projects` (view) mengambil data dan memasukkannya ke context, lalu template `projects.html` merender data. Ini artinya data tidak di-*hardcode* di HTML, tetapi get dari database.

2. Perbedaan utama antara section Experience (Tutorial 02) dan Projects (Tugas 2) terletak pada tipe datanya: model `Experience` memiliki field tanggal (`started_at`, `ended_at`) serta properti `is_ongoing` untuk status, sedangkan model `Project` menyimpan `tech_stack` dan `link`. Pola MVT-nya tetap sama saja, tetapi field dan tampilannya yang disesuaikan.

3. Migrasi Django membuat perubahan model terstruktur dan mudah diterapkan. Kedua command tersebut memastikan struktur database selalu sinkron dengan definisi model tanpa perlu menulis SQL secara manual.

## AI Disclosure

Pengerjaan tugas ini dibantu oleh AI. 
Tool(s) yang digunakan: 
- **opencode**

Model(s) yang digunakan:
- **deepseek-v4-flash**

Bagian yang dibantu:

- Menyusun model `Project`, view `show_projects`, routing `main:show_projects`, dan template `projects.html` mengikuti pola MVT section Experience.
- Menulis CSS untuk tata letak kartu section Projects agar konsisten dengan style yang ada.
- Membantu menyusun dan memformat README.

Semua perubahan yang dilakukan oleh AI telah melewati proses review secara manual oleh saya.