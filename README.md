# Diagram Voronoi dengan Algoritma Fortune

Tugas Pemrograman 2 Geometri Komputasional. Aplikasi desktop ini menggunakan Tkinter untuk menerima titik dan menampilkan hasil perhitungan modul Fortune.

## Members
* Nathanael Leander Herdanatra - 2406421320
* Hasanul Muttaqin - 2406413331

## Menjalankan aplikasi

Gunakan Python 3.10 atau lebih baru dengan Tkinter. Jalankan dari folder proyek.

```bash
python main.py
```

## Menggunakan GUI

Saat dibuka, bidang kosong. Pilih **File → Muat contoh 25 titik** untuk mencoba data bawaan.

- Pilih **File → Buka file TXT…** atau tekan `Ctrl+O` untuk memuat titik dari file.
- Klik kiri pada bidang untuk menambah titik. Klik kanan di dekat titik untuk menghapusnya.
- Pilih **File → Hapus** atau tekan `Ctrl+Z` untuk membatalkan perubahan terakhir. Pilih **File → Hapus semua** untuk mengosongkan bidang.
- Pilih **Edit → Bounding box…** untuk mengatur batas minimum dan maksimum sumbu X dan Y. Batas pilihan juga dipakai saat membuka file titik.
- Tekan `Ctrl++` atau `Ctrl+-` untuk memperbesar atau memperkecil bidang. Geser tampilan lewat scrollbar atau roda mouse. Tahan `Shift` saat menggulir untuk menggeser secara horizontal.
- Tekan **Play** atau `F5`. Sweep line bergerak dari atas ke bawah dan breakpoint pada beach line meninggalkan jejak sisi Voronoi. Penghitung di kiri bertambah saat titik diproses, sisi terbentuk, dan sel selesai. Warna sel muncul saat animasi berakhir.
- Gunakan menu **Tampilan** untuk mengatur visibilitas lingkaran kosong terbesar.

## Format file titik

Tulis satu pasangan koordinat `x y` per baris. Gunakan spasi atau koma sebagai pemisah dan titik untuk desimal. Baris kosong serta komentar yang diawali `#` boleh disertakan. Koordinat identik hanya dimuat sekali.

```text
# x y
120 80
310, 175
540.5 340
```

Sumbu `x` bertambah ke kanan dan sumbu `y` bertambah ke bawah. Jika batas belum diatur melalui menu Edit, GUI menyesuaikan bounding box bila koordinat file berada di luar bidang bawaan.

## Cara kerja

Sapuan Fortune memproses peristiwa titik dan lingkaran untuk menemukan pasangan titik yang selnya bertetangga. Setiap sel dibentuk dengan memotong bounding box pada garis bagi tegak lurus antara titik dan tetangganya. Lingkaran kosong terbesar dipilih dari peristiwa lingkaran yang pusatnya berada di dalam bounding box.

Saat diputar, setiap sisi digambar hanya pada bagian yang sudah dijangkau beach line. Referensi visualisasi: [Fortune's Algorithm, Tufts COMP 163](https://www.eecs.tufts.edu/~vporok01/c163/).

## Bantuan AI

Gemini 3.6 Flash digunakan untuk membantu memahami dan generasi awal struktur data dan algoritma Fortune
OpenAI Codex digunakan untuk membantu membuat GUI Tkinter dan titik masuk aplikasi (`gui.py` dan `main.py`)