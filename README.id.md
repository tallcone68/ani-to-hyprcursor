# ANI ke Hyprcursor Converter

Mengubah cursor animasi Windows `.ani` menjadi **theme Hyprcursor native** untuk Hyprland.

Converter ini dibuat generik: tidak di-hardcode khusus untuk Furina, Skirk, atau cursor pack tertentu.

## Fitur

- Mengubah file cursor `.ani` menjadi format Hyprcursor native.
- Mempertahankan animasi dan timing setiap frame.
- Otomatis memetakan nama cursor umum ke shape Hyprcursor standar.
- Menangani nama cursor yang bentrok secara otomatis.
- Membuat berbagai ukuran cursor dari **12 px sampai 64 px**.
- Membuat alias cursor resize seperti `left_side`, `right_side`, `top_side`, dan corner.
- Theme bisa langsung diaktifkan dengan `hyprctl setcursor`.
- Membuat backup ketika mengganti theme hasil converter yang sudah ada.

## Persyaratan

Paket Arch Linux:

```bash
sudo pacman -S python-pillow hyprcursor
```

Python 3 diperlukan.

## Instalasi / Penggunaan

Simpan script di lokasi yang mudah digunakan:

```bash
mkdir -p ~/.local/bin
cp ani_to_hyprcursor.py ~/.local/bin/
chmod +x ~/.local/bin/ani_to_hyprcursor.py
```

Masuk ke folder yang berisi file `.ani`, atau berikan folder tersebut sebagai argumen:

```bash
python3 ~/.local/bin/ani_to_hyprcursor.py "/path/to/Cursor Pack"
```

Jika tidak memberikan folder sumber, jalankan script dari folder cursor pack:

```bash
python3 ani_to_hyprcursor.py
```

Theme hasil converter dipasang di:

```text
~/.local/share/icons/<Nama Theme>/
```

Kemudian aktifkan:

```bash
hyprctl setcursor "Nama Theme" 32
```

Angka `32` bisa diganti dengan ukuran yang tersedia dari 12 sampai 64.

## Mengganti Cursor Theme

Tidak perlu menjalankan converter lagi hanya untuk mengganti theme.

Contoh:

```bash
hyprctl setcursor "Furina 2.0" 32
```

Kemudian ganti ke theme lain:

```bash
hyprctl setcursor "Skirk Cursor" 48
```

Nama theme harus sama persis dengan nama theme yang terpasang.

## Konfigurasi Hyprland

Untuk menggunakan Hyprcursor native:

```lua
cursor = {
    enable_hyprcursor = true,
}
```

Atur environment variable di konfigurasi Lua Hyprland:

```lua
hl.env("HYPRCURSOR_THEME", "Furina 2.0")
hl.env("HYPRCURSOR_SIZE", "32")
```

Setelah mengubah konfigurasi, restart/reload Hyprland sesuai kebutuhan.

## Menghapus Cursor Theme

Pertama pindah ke cursor theme lain:

```bash
hyprctl setcursor "Adwaita" 32
```

Kemudian hapus folder theme yang dihasilkan converter.

Contoh:

```bash
rm -rf ~/.local/share/icons/"Skirk Cursor"
```

Atau:

```bash
rm -rf ~/.local/share/icons/"Furina 2.0"
```

Jika tidak yakin nama theme yang terpasang, lihat daftar theme lokal terlebih dahulu:

```bash
find ~/.local/share/icons -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort
```

Hanya hapus theme custom/generated yang kamu kenali. **Jangan menghapus** theme sistem dari `/usr/share/icons/`.

Biasanya tidak perlu reboot setelah menghapus theme.

## Nama Cursor yang Bentrok

Beberapa `.ani` pack memiliki beberapa file yang terdeteksi sebagai shape cursor standar yang sama.

Contohnya:

```text
Skirk link.ani
Skirk normal.ani
```

keduanya mungkin awalnya terdeteksi sebagai shape standar yang sudah digunakan.

Converter otomatis mempertahankan mapping standar pertama dan memberikan nama unik untuk collision berikutnya, misalnya:

```text
[INFO] Skirk link.ani: 'pointer' bentrok, menggunakan nama unik 'skirk-link'
```

Untuk collision biasa, tidak perlu mengedit `cursor-map.json` secara manual.

## Output

Converter menampilkan:

- folder sumber
- nama theme
- jumlah file `.ani`
- ukuran yang dibuat
- progress konversi
- lokasi backup
- jumlah berhasil/gagal

Jika konversi berhasil, aktifkan theme:

```bash
hyprctl setcursor "Nama Theme" 32
```

## Troubleshooting

### Cursor tidak langsung berubah

Jalankan:

```bash
hyprctl setcursor "Nama Theme" 32
```

Pastikan nama theme benar.

### Ada bentuk cursor yang tidak muncul

Converter otomatis memetakan nama `.ani` yang umum. Nama cursor yang sangat tidak umum mungkin membutuhkan mapping khusus menggunakan `cursor-map.json`.

### Hyprland masih menggunakan cursor lain

Periksa:

```bash
hyprctl getoption cursor:enable_hyprcursor
```

Untuk theme Hyprcursor native, hasilnya seharusnya:

```text
bool: true
```

Pastikan juga nilai `HYPRCURSOR_THEME` dan `HYPRCURSOR_SIZE` sudah benar.

## Catatan

Converter ini ditujukan untuk cursor pack `.ani` dan Hyprcursor native pada Hyprland. Aplikasi yang tidak menggunakan Hyprcursor dapat menggunakan mekanisme cursor mereka sendiri atau fallback XCursor.
