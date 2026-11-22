# Diagram Voronoi dengan Algoritma Fortune

Tugas Pemrograman 2 Geometri Komputasional. Aplikasi desktop ini menggunakan Tkinter untuk menerima titik dan menampilkan hasil perhitungan modul Fortune.

## Menjalankan aplikasi

Gunakan Python 3.10 atau lebih baru dengan Tkinter. Jalankan dari folder proyek.

```bash
python main.py
```

## Menggunakan GUI

Saat dibuka, aplikasi langsung memuat contoh bawaan dengan 25 titik.

- Pilih **Buka file TXT…** atau tekan `Ctrl+O` untuk memuat dan menghitung diagram dari file.
- Klik kiri pada bidang untuk menambah titik. Klik kanan di dekat titik untuk menghapusnya.
- Setelah mengedit titik dengan mouse, pilih **Hitung Voronoi** atau tekan `F5`.
- Pilih **Kosongkan** untuk memulai ulang dengan bidang kosong, atau **Muat contoh 25 titik** untuk mengembalikan contoh bawaan.
- Gunakan **Tampilkan lingkaran** untuk menampilkan atau menyembunyikan lingkaran kosong terbesar.

## Format file titik

Tulis satu pasangan koordinat `x y` per baris. Gunakan spasi atau koma sebagai pemisah dan titik untuk desimal. Baris kosong serta komentar yang diawali `#` boleh disertakan. Koordinat identik hanya dimuat sekali.

```text
# x y
120 80
310, 175
540.5 340
```

Sumbu `x` bertambah ke kanan dan sumbu `y` bertambah ke bawah. GUI menyesuaikan bounding box bila koordinat file berada di luar bidang bawaan.

## Keterbatasan saat ini

Pada contoh bawaan, modul Fortune hanya mengembalikan segmen dengan panjang nol. GUI mengabaikan segmen tersebut, sehingga titik dan lingkaran terlihat dengan jumlah sisi 0.

## Pengungkapan bantuan AI

OpenAI Codex digunakan untuk membantu membuat GUI Tkinter dan titik masuk aplikasi (`gui.py` dan `main.py`)