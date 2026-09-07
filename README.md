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

1. Struktur halaman tersusun dari <header>, <nav>, <main>, <section>, <article>, dan <footer>. Elemen semantik HTML5 akan membuat struktur website lebih terstruktur dan mudah untuk dibaca manusia maupun robot search engine.

2. Tantangan utama dari mengatur CSS website agar tetap responsive adalah ketika berhadapan dengan platform mobile atau layar kecil. Solusi dari tantangan ini adalah menggunakan fungsi clamp pada teks dan juga jarak antar section diperbesar.

3. Batasan yang saya alami ketika membuat web dengan gaya static web murni ini adalah semua konten harus ditulis secara manual dan *hardcoded* dalam konten HTML atau CSS itu sendiri. Saya juga tidak bisa membuat efek-efek visual yang memerlukan depedensi-dependensi lain dari elemen-elemen static web yang digunakan saat ini.

## AI Disclosure

Pengerjaan tugas ini dibantu oleh AI. 
Tool(s) yang digunakan: 
- **opencode**

Model(s) yang digunakan:
- **deepseek-v4-flash**

Bagian yang dibantu:

- Memperbaiki struktur HTML untuk section tiga item Skills dan section Projects.
- Menulis aturan CSS untuk tata letak kartu (grid), styling, dan breakpoint responsif.
- Membantu menyusun dan memformat README.

Semua perubahan yang dilakukan oleh AI telah melewati proses review secara manual oleh saya.