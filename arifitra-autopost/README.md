# Kantor ASN Go Digital: Robot Posting + Bot Telegram + Kantor 3D

Paket ini berisi tiga bagian yang bekerja bersama untuk @arifitra_muhammad:

| Bagian | Fungsinya | Biaya |
|---|---|---|
| **Robot posting** (`scripts/publish.py`) | Menerbitkan carousel ke Instagram, Threads, dan Halaman Facebook sesuai jadwal | Gratis |
| **Bot Telegram** (`bot/`) | Memerintah 12 karyawan AI dari HP: produksi carousel, revisi, setujui, jadwalkan, beri tugas | GitHub gratis; otak Claude via API berbayar per pemakaian, atau Gemini tier gratis |
| **Kantor 3D** (`docs/`) | Monitor 3D Lantai 2 di GitHub Pages; status karyawan berubah mengikuti perintah dari Telegram | Gratis |

Repo publik di GitHub mendapat menit GitHub Actions gratis, dan API resmi Meta untuk Instagram serta Threads juga gratis.

## Cara 1: perintah dari Telegram

```
/produksi desa jual:naskah perbedaan Musdes dan Musrenbangdes
```
Dalam beberapa menit, bot mengirim 5 slide, caption IG/Threads/FB, dan catatan cek fakta. Setelah itu tekan **Setujui**, **Terbitkan sekarang**, atau **Buang draf**.

- **Bahan berita/pasal:** teruskan (forward) beritanya ke bot, lalu balas (reply) pesan itu dengan `/produksi`. Teks berita jadi sumber riset.
- **Foto sampul:** kirim foto dengan caption `/produksi topik`.
- **Revisi:** `/revisi 1127-2010 slide 3 terlalu panjang, ganti judul sampul`
- **Jadwal:** `/setuju 1127-2010 2026-12-01 19:30`, `/setuju 1127-2010 19:30`, atau `/setuju 1127-2010 sekarang`
- **Satu karyawan:** `/tugas hendra tulis promo Simulasi CAT CPNS untuk story`. Balas jawabannya untuk melanjutkan obrolan dengan karyawan yang sama.
- **Lainnya:** `/antrean`, `/batal FOLDER`, `/terbitkan`, `/kantor` (berisi tombol **Buka Kantor 3D**), `/bantuan`.
- Pesan biasa tanpa garis miring dijawab Sinta, resepsionis Anda.

Bot hanya menjawab Anda (dikunci ke `TELEGRAM_OWNER_ID`).

**Kecepatan respons:** bot berjalan di GitHub Actions dalam putaran sekitar 5 menit yang disambung terus-menerus. Biasanya bot menjawab dalam hitungan detik. Pada pergantian putaran atau saat GitHub sedang padat, jawaban bisa tertunda beberapa menit. Pesan tidak hilang; pesan itu diproses di putaran berikutnya.

## Cara 2: dari Kantor ASN Go Digital (Claude)

1. Buka **Kantor ASN Go Digital**, lalu klik **Jalankan produksi**.
2. Periksa slide dan caption, lalu baca daftar **Cek fakta Bu Ratna**. Cek setiap nomor peraturan ke JDIH.
3. Klik **Unduh paket posting (.zip)** dan ekstrak.
4. Unggah foldernya ke `queue/` di repo ini. Di GitHub, buka **Add file → Upload files** dan seret foldernya ke sana.
5. Selesai. Setiap 30 menit robot mengecek antrean. Begitu `publish_at` tiba, carousel langsung terbit.

Isi folder:

```
queue/2026-11-28_0730_ai-asisten-kerja-asn/
  slide-1.jpg … slide-5.jpg
  post.json        ← jadwal + caption IG/Threads/FB + komentar pertama + alt text
  status.json      ← dibuat robot: ID postingan atau pesan error per platform
```

Untuk menunda atau membatalkan, ubah `publish_at` di `post.json` atau hapus foldernya sebelum jamnya tiba. Untuk mematikan satu platform, ubah nilainya di `"platforms"` menjadi `false`.

## Setup sekali saja (±1 jam)

> Langkah 1–6 menyiapkan robot posting. Langkah 7–9 menyiapkan bot Telegram dan Kantor 3D.

### 1. Repo GitHub
- Buat repo **publik** baru, misalnya `arifitra-autopost`, lalu unggah semua isi paket ini.
- Repo harus publik karena Meta mengambil gambar lewat URL `raw.githubusercontent.com`. Akibatnya, slide yang sudah ada di antrean bisa dilihat orang sebelum terbit. Jangan taruh dokumen dinas atau data pribadi di repo ini.

### 2. Instagram (gratis, resmi)
1. Di aplikasi Instagram, buka **Pengaturan → Jenis akun dan alat → Beralih ke akun profesional → Kreator**.
2. Buka developers.facebook.com, pilih **My Apps → Create App**, lalu gunakan use case **Instagram API with Instagram Login**.
3. Tambahkan akun @arifitra_muhammad sebagai *Instagram Tester*, lalu terima undangannya dari aplikasi Instagram (Pengaturan → Aplikasi dan situs web).
4. Buat token dengan izin `instagram_business_basic`, `instagram_business_content_publish`, dan `instagram_business_manage_comments`. Tukar token itu menjadi **long-lived token** (berlaku ±60 hari).
5. Salin **Instagram User ID** dan token.

> Akun yang Anda kelola sendiri sebagai tester aplikasi Anda bisa langsung dipakai tanpa App Review.

### 3. Threads (gratis, resmi)
1. Di aplikasi yang sama, tambahkan use case **Access the Threads API**.
2. Tambahkan @arifitra_muhammad sebagai *Threads Tester*, lalu terima undangannya di Threads.
3. Buat token dengan izin `threads_basic` dan `threads_content_publish`, lalu tukar menjadi long-lived token.
4. Salin **Threads User ID** dan token.

### 4. Facebook: penting
**Profil pribadi Facebook (facebook.com/arief.181814) tidak bisa diposting lewat API apa pun.** Meta menutup akses itu sejak 2018. Pilihannya:
- **Disarankan:** buat **Halaman Facebook** "Arif Itra Muhammad – ASN Go Digital". Robot bisa memposting ke Halaman, lalu bagikan postingan itu ke profil Anda dengan satu klik.
- Atau tetap memposting manual: salin caption Facebook dari kantor virtual dan unggah 5 slide (sekitar 1 menit).

Kalau memakai Halaman, Anda butuh **Page ID** dan **Page Access Token** dari token pengguna long-lived dengan izin `pages_manage_posts` dan `pages_read_engagement`. Token Halaman yang dibuat dari token long-lived tidak kedaluwarsa.

### 5. Simpan rahasia di GitHub
Buka **Settings → Secrets and variables → Actions → New repository secret**, lalu isi:

| Secret | Isi |
|---|---|
| `IG_USER_ID`, `IG_TOKEN` | dari langkah 2 |
| `THREADS_USER_ID`, `THREADS_TOKEN` | dari langkah 3 |
| `FB_PAGE_ID`, `FB_PAGE_TOKEN` | dari langkah 4 (boleh dikosongkan) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID` | dari langkah 7 |
| `ANTHROPIC_API_KEY` atau `GEMINI_API_KEY` | dari langkah 8 |
| `GH_PAT` | fine-grained token GitHub untuk repo ini dengan izin **Secrets: Read and write**, supaya token Meta bisa diperpanjang otomatis |

Platform yang secret-nya kosong akan dilewati, tidak dianggap error.

### 6. Uji coba
Buka **Actions → Robot Posting → Run workflow**, isi `dry_run = 1`. Log akan menampilkan folder yang siap terbit tanpa benar-benar memposting. Setelah itu, jalankan sekali dengan `0` untuk satu konten uji.

### 7. Bot Telegram
1. Di Telegram, chat **@BotFather**, kirim `/newbot`, lalu beri nama misalnya "Kantor ASN Go Digital". Salin token bot.
2. Simpan sebagai secret `TELEGRAM_BOT_TOKEN`.
3. Jalankan **Actions → Bot Telegram Kantor → Run workflow**, lalu kirim pesan apa saja ke bot Anda. Bot membalas dengan **Chat ID** Anda.
4. Simpan angka itu sebagai secret `TELEGRAM_OWNER_ID`. Mulai saat itu bot hanya melayani Anda.
5. (Opsional) Di BotFather, gunakan `/setcommands` untuk menempelkan daftar perintah supaya muncul sebagai menu:
```
produksi - Buat carousel baru
revisi - Revisi draf
setuju - Jadwalkan draf
antrean - Lihat draf dan jadwal
batal - Batalkan jadwal
terbitkan - Jalankan robot posting
tugas - Perintah satu karyawan
kantor - Status tim + kantor 3D
bantuan - Daftar perintah
```

### 8. Otak tim (pilih salah satu)
- **Claude (disarankan, sama dengan kantor di Claude):** buat API key di console.anthropic.com, isi saldo, lalu simpan sebagai secret `ANTHROPIC_API_KEY`. Pemakaian API ditagih terpisah dari langganan Claude Anda, per pemakaian. Pantau pengeluarannya di console dan pasang batas belanja bulanan. Model bisa diatur lewat variabel repo `CLAUDE_MODEL` (default `claude-sonnet-5-5`). Untuk tugas ringan, isi `claude-haiku-5-5` supaya lebih hemat.
- **Gratis:** buat API key Gemini di Google AI Studio, lalu simpan sebagai `GEMINI_API_KEY`. Key ini hanya dipakai bila `ANTHROPIC_API_KEY` kosong. Kuota gratisnya terbatas dan bisa berubah sewaktu-waktu.

### 9. Kantor 3D di GitHub Pages
1. Buka **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Jalankan **Actions → Kantor 3D (GitHub Pages) → Run workflow**.
3. Alamatnya `https://NAMA-ANDA.github.io/arifitra-autopost/`. Tombol **Buka Kantor 3D** di `/kantor` langsung mengarah ke sana. Kalau alamatnya berbeda, isi variabel repo `PAGES_URL`.
4. Monitor membaca `state/office.json` setiap 30 detik. Karyawan yang sedang bekerja menyalakan lampu meja dan cincin kuning, lalu berubah hijau setelah selesai.

> Karena repo publik, isi `drafts/`, `queue/`, dan `state/` (draf carousel, jadwal, log aktivitas) bisa dilihat orang yang tahu alamat repo. Jangan kirim dokumen dinas atau data pribadi ke bot.

## Perawatan
- **Perpanjang Token** berjalan otomatis tanggal 1 dan 15 setiap bulan. Kalau gagal (misalnya token sudah keburu kedaluwarsa), buat token baru seperti di langkah 2 dan 3.
- GitHub bisa menonaktifkan jadwal otomatis pada repo yang lama tidak ada aktivitas (sekitar 60 hari). Mengunggah konten secara rutin menjaga robot tetap aktif. Kalau terlanjur nonaktif, aktifkan lagi di tab Actions.
- Batas API Meta jauh di atas kebutuhan: satu carousel dihitung sebagai satu postingan.
- Kalau postingan gagal, buka `status.json` di folder itu untuk melihat pesan error-nya. Robot akan mencoba lagi 30 menit kemudian tanpa menerbitkan ulang platform yang sudah berhasil.
- Kalau Meta meminta versi API tertentu, isi variabel repo `GRAPH_VERSION` (mis. `v24.0`) di **Settings → Variables**.

## Rambu konten
Akun ini milik ASN. Robot hanya menerbitkan apa yang sudah Anda setujui di kantor virtual. Tetap jaga netralitas politik, jangan memakai data internal dinas, dan pastikan setiap nomor peraturan sudah dicek ke JDIH sebelum folder diunggah.
