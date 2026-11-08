# Program-Visualisasi-Step-by-Step-Penyelesaian-Fifteen-Puzzle-dengan-BA-dan-Hybrid-Heuristic

Program visualisasi *step-by-step* penyelesaian **Fifteen Puzzle** menggunakan **Bidirectional A\* (BA\*)** dan **Hybrid Heuristic** (*Manhattan Distance*, *Linear Conflict*, dan *Walking Distance*), lengkap dengan antarmuka grafis (GUI) berbasis Tkinter.

---

## Daftar Isi

- [Tentang Program](#tentang-program)
- [Fitur](#fitur)
- [Cara Kerja Algoritma](#cara-kerja-algoritma)
- [Persyaratan](#persyaratan)
- [Cara Menjalankan](#cara-menjalankan)
- [Cara Penggunaan](#cara-penggunaan)
- [Struktur Kode](#struktur-kode)
- [Parameter yang Dapat Diubah](#parameter-yang-dapat-diubah)
- [Keterbatasan](#keterbatasan)

---

## Tentang Program

Fifteen Puzzle adalah puzzle geser berukuran 4×4 dengan 15 tile bernomor dan satu kotak kosong (*blank*). Tujuannya adalah menyusun tile secara berurutan sehingga mencapai konfigurasi **Goal**:

```
 1  2  3  4
 5  6  7  8
 9 10 11 12
13 14 15  _
```

Program ini mencari solusi dengan algoritma **Bidirectional A\*** yang menelusuri ruang pencarian dari dua arah sekaligus (dari *Start* menuju *Goal* dan dari *Goal* menuju *Start*) hingga kedua pencarian bertemu. Seluruh proses pencarian direkam sehingga dapat dipelajari iterasi demi iterasi, bukan hanya hasil akhirnya.

## Fitur

- **Pencarian Bidirectional A\*** dengan dua sisi (*Forward* dan *Backward*), masing-masing memiliki `OpenList` dan `ClosedList` sendiri.
- **Hybrid Heuristic**: `HH = MD / 3 + WD + LC`.
- **Validasi input**: memeriksa bahwa angka 0–15 muncul tepat satu kali dan bahwa puzzle dapat diselesaikan (*solvable*) menggunakan paritas inversi.
- **GUI dengan dua tab**:
  - **Langkah solusi** – animasi dan daftar langkah dari posisi awal sampai Goal.
  - **Proses pencarian BA\*** – penjelasan tiap iterasi: state yang diekspansi, anak yang dihasilkan, nilai `g`, `MD`, `WD`, `LC`, `HH`, `F`, serta ukuran `OpenList` dan `ClosedList`.
- **Kontrol pemutaran**: mulai/jeda, maju, mundur, lompat ke awal/akhir, dan pengaturan kecepatan animasi.
- **Pewarnaan tile**: hijau = sudah di posisi benar, abu-abu = belum benar, oranye = tile yang baru digeser.
- **Pewarnaan sisi pencarian**: latar biru untuk *Forward* dan ungu untuk *Backward*.
- **Mode contoh dan acak**: tombol untuk mengisi puzzle contoh atau puzzle acak yang dijamin solvable.
- **Pencarian di *thread* terpisah** sehingga GUI tidak menggantung saat menghitung.
- **Perekaman hemat memori**: hanya menyimpan 200 iterasi pertama dan 200 iterasi terakhir; iterasi di tengah diringkas.

## Cara Kerja Algoritma

### 1. Bidirectional A\*

Pencarian dijalankan bergantian antara sisi *Forward* dan *Backward*:

1. Giliran pertama diberi jatah `75.000` ekspansi, giliran berikutnya `15.000` ekspansi per siklus.
2. Pada tiap ekspansi, node dengan nilai `F = g + HH` terkecil diambil dari `OpenList`.
3. Setiap anak yang belum ada di `ClosedList` sisi sendiri dimasukkan ke `OpenList`.
4. Jika sebuah anak sudah ada di `ClosedList` sisi lawan, itu adalah **titik temu**; jalur solusi dibentuk dengan menggabungkan jalur *Forward* dan jalur *Backward* yang dibalik.

### 2. Hybrid Heuristic

| Komponen | Penjelasan |
|---|---|
| **Manhattan Distance (MD)** | Jumlah jarak baris + kolom setiap tile ke posisi targetnya. Dalam rumus hibrida, nilainya dibagi 3. |
| **Linear Conflict (LC)** | Tambahan `2` untuk tiap tile yang saling menghalangi dalam satu baris/kolom yang sama dengan posisi targetnya; dihitung dengan *Longest Increasing Subsequence* (LIS). |
| **Walking Distance (WD)** | Perkiraan jumlah langkah minimum pada representasi abstrak baris dan kolom. Tabel dibangun satu kali dengan BFS dari state Goal, lalu dipakai sebagai *lookup table*. |

```
HH = MD / 3 + WD + LC
```

### 3. Nama State pada Visualisasi

State diberi nama agar mudah diikuti: `S` untuk Start, `Goal` untuk Goal, lalu `A`, `B`, `C`, ... untuk state lain sesuai urutan kemunculannya.

## Persyaratan

- **Python 3.8+**
- **Tkinter** (sudah termasuk pada instalasi Python standar di Windows dan macOS)

Tidak ada pustaka eksternal yang perlu dipasang. Seluruh modul yang digunakan adalah bawaan Python: `heapq`, `random`, `collections`, `functools`, `time`, `threading`, dan `tkinter`.

Pada beberapa distribusi Linux, Tkinter perlu dipasang terpisah:

```bash
# Debian / Ubuntu
sudo apt install python3-tk
```

## Cara Menjalankan

```bash
# 1. Clone repositori
git clone https://github.com/<username>/Program-Visualisasi-Step-by-Step-Penyelesaian-Fifteen-Puzzle-dengan-BA-dan-Hybrid-Heuristic.git
cd Program-Visualisasi-Step-by-Step-Penyelesaian-Fifteen-Puzzle-dengan-BA-dan-Hybrid-Heuristic

# 2. Jalankan program
python fifteen_puzzle_gui.py
```

## Cara Penggunaan

1. **Isi puzzle** pada kolom input 4×4. Gunakan angka `0`–`15`; kolom kosong atau `0` berarti *blank*. Atau klik:
   - **Contoh** untuk memuat puzzle contoh, atau
   - **Acak** untuk membuat puzzle acak yang pasti solvable.
2. Klik **Selesaikan**. Status pencarian tampil di bawah papan.
3. Setelah solusi ditemukan, gunakan tab **Langkah solusi**:
   - Tombol `|<`, `< Mundur`, `Putar/Jeda`, `Maju >` untuk menelusuri langkah.
   - Klik salah satu langkah pada daftar untuk langsung melompat ke langkah tersebut.
   - Atur *slider* **Jeda antar langkah (ms)** untuk mengubah kecepatan animasi.
4. Buka tab **Proses pencarian BA\*** untuk melihat detail tiap iterasi: state yang diekspansi, anak-anaknya beserta nilai heuristiknya, dan ukuran `OpenList`/`ClosedList` kedua sisi.

### Contoh Input

```
 1  2  3  4
 5  _  6  8
 9 10  7 12
13 14 11 15
```

### Contoh Pesan Status

```
Selesai: N langkah | ekspansi f/b = X/Y | Z s
Tab proses menampilkan M dari K iterasi.
```

## Struktur Kode

```
fifteen_puzzle_gui.py
├── Dasar puzzle
│   ├── GOAL, DIRECTIONS         # state tujuan dan arah gerak blank
│   ├── neighbors()              # membangkitkan state tetangga
│   ├── is_solvable()            # cek solvability lewat paritas inversi
│   ├── validate_state()         # validasi isi puzzle
│   └── make_scramble()          # membuat puzzle acak dari Goal
├── Heuristic                    # MD, LC, WD (tabel BFS), dan HH
├── Side, Namer, Recorder        # struktur satu sisi pencarian, penamaan state, perekam iterasi
├── bidirectional_astar()        # inti algoritma BA*
├── build_path(), validate_path()# pembentukan dan validasi jalur solusi
├── teks_event()                 # mengubah rekaman iterasi menjadi teks penjelasan
└── App                          # GUI Tkinter (tab solusi dan tab proses pencarian)
```

Fungsi `bidirectional_astar(..., trace=True)` juga dapat dipakai langsung dari kode untuk mencetak jejak iterasi ke terminal tanpa GUI.

## Parameter yang Dapat Diubah

| Parameter | Lokasi | Nilai Default | Fungsi |
|---|---|---|---|
| `MAX_EXPANSIONS` | konstanta GUI | `400_000` | Batas total ekspansi sebelum pencarian dihentikan |
| `first_limit` | `bidirectional_astar()` | `75_000` | Jatah ekspansi pada giliran pertama |
| `cycle_limit` | `bidirectional_astar()` | `15_000` | Jatah ekspansi pada giliran berikutnya |
| `head_limit`, `tail_limit` | `Recorder` | `200`, `200` | Jumlah iterasi awal dan akhir yang direkam untuk visualisasi |
| `CELL`, `CELL_S` | konstanta GUI | `70`, `44` | Ukuran kotak papan solusi dan papan proses |

## Keterbatasan

- Puzzle yang sangat sulit dapat melebihi batas `MAX_EXPANSIONS`; program akan menampilkan pesan agar mencoba puzzle yang lebih mudah, atau naikkan batas tersebut dengan konsekuensi waktu dan memori yang lebih besar.
- Karena heuristik yang dipakai bersifat hibrida (`MD / 3 + WD + LC`) dan pencarian dua arah berhenti pada titik temu pertama, panjang solusi yang dihasilkan tidak selalu dijamin minimum.
- Pada tab proses pencarian, hanya 200 iterasi pertama dan 200 iterasi terakhir yang ditampilkan agar penggunaan memori tetap ringan.

---

**Kata kunci:** Fifteen Puzzle · Bidirectional A\* · Hybrid Heuristic · Manhattan Distance · Linear Conflict · Walking Distance · Tkinter · Visualisasi Algoritma
