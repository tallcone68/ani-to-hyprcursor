# ANI to Hyprcursor

Converter generik untuk mengubah cursor Windows **`.ani` (Animated Cursor)**
menjadi **native Hyprcursor** untuk Hyprland.

Tujuannya sederhana: satu script bisa dipakai ulang untuk banyak cursor pack,
bukan hanya Furina.

## Fitur

- Semua file `.ani` dalam satu folder diproses otomatis.
- Animasi dan timing dari ANI dipertahankan.
- Ukuran bawaan: **12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64 px**.
- Hyprcursor melakukan scaling untuk ukuran yang tidak tersedia. Hyprcursor mendukung
  `resize_algorithm = bilinear`, `nearest`, atau `none`. [Dokumentasi Hyprcursor](https://github.com/hyprwm/hyprcursor/blob/main/docs/MAKING_THEMES.md)
- Nama cursor umum seperti normal, hand, text, move, horz, vert, dgn1, dan dgn2
  dikenali otomatis.
- Alias resize Hyprland seperti `left_side`, `right_side`, `top_side`,
  `bottom_side`, dan corner resize dibuat melalui `define_override`.
- Theme baru dibangun di direktori sementara terlebih dahulu. Theme aktif baru
  diganti jika seluruh proses berhasil.
- Jika theme dengan nama yang sama sudah ada, script membuat backup:
  `THEME backup-before-hyprcursor`.

## Dependensi Arch Linux

```bash
sudo pacman -S python-pillow hyprcursor
```

`hyprcursor-util` adalah utilitas resmi untuk membuat/compile theme Hyprcursor,
dan `xcur2png` merupakan runtime dependency dari utilitas tersebut. [README hyprcursor-util](https://github.com/hyprwm/hyprcursor/blob/main/hyprcursor-util/README.md)

Jika `hyprcursor-util` belum tersedia setelah instalasi, cek:

```bash
command -v hyprcursor-util
```

## Instalasi script

Simpan:

```text
ani_to_hyprcursor.py
README.md
```

di folder yang sama, misalnya:

```text
~/Downloads/ani-to-hyprcursor/
```

Buat executable jika mau:

```bash
chmod +x ani_to_hyprcursor.py
```

## Convert cursor pack

Misalnya cursor pack ini:

```text
~/Downloads/MyCursor/
├── normal.ani
├── busy.ani
├── hand.ani
├── text.ani
├── horz.ani
├── vert.ani
└── ...
```

Jalankan:

```bash
python ani_to_hyprcursor.py ~/Downloads/MyCursor
```

Nama theme secara default mengikuti nama folder:

```text
MyCursor
```

Theme akan dipasang ke:

```text
~/.local/share/icons/MyCursor/
```

Kemudian aktifkan:

```bash
hyprctl setcursor "MyCursor" 32
```

Hyprcursor memang mendukung pemasangan theme di `~/.local/share/icons`
dan pengaturan theme/size melalui `HYPRCURSOR_THEME`, `HYPRCURSOR_SIZE`,
atau `hyprctl setcursor`. [Hyprland Wiki](https://wiki.hypr.land/hypr-ecosystem/user/hyprcursor/)

## Memberi nama theme sendiri

```bash
python ani_to_hyprcursor.py ~/Downloads/MyCursor --theme "My Awesome Cursor"
```

Hasil:

```text
~/.local/share/icons/My Awesome Cursor/
```

Aktifkan:

```bash
hyprctl setcursor "My Awesome Cursor" 32
```

## Mengubah daftar ukuran

Default:

```text
12,16,20,24,28,32,36,40,44,48,52,56,60,64
```

Kalau mau lebih sedikit:

```bash
python ani_to_hyprcursor.py ~/Downloads/MyCursor \
  --sizes 16,24,32,48,64
```

Kalau mau ukuran lebih banyak:

```bash
python ani_to_hyprcursor.py ~/Downloads/MyCursor \
  --sizes 12,16,20,24,28,32,36,40,44,48,52,56,60,64
```

Tidak perlu membuat setiap ukuran secara manual setelah itu; Hyprcursor dapat
memilih ukuran yang tersedia atau melakukan resize sesuai `resize_algorithm`.

## Jika nama `.ani` aneh

Script melakukan deteksi berdasarkan nama file.

Contoh nama yang langsung dikenali:

```text
normal.ani
busy.ani
hand.ani
text.ani
move.ani
link.ani
help.ani
horz.ani
vert.ani
dgn1.ani
dgn2.ani
precision.ani
unavailable.ani
```

Nama seperti:

```text
Furina normal.ani
Furina horz.ani
Furina dgn1.ani
```

juga dikenali.

Untuk pack lain yang memakai nama berbeda, gunakan `cursor-map.json`.

## cursor-map.json

Buat file `cursor-map.json` di folder `.ani`:

```json
{
  "My Arrow.ani": {
    "name": "left_ptr",
    "aliases": "arrow default top_left_arrow dnd-none X_cursor"
  },
  "My Horizontal Resize.ani": {
    "name": "ew-resize",
    "aliases": "ew-resize e-resize w-resize col-resize left_side right_side h_double_arrow sb_h_double_arrow size_hor"
  },
  "My Vertical Resize.ani": {
    "name": "ns-resize",
    "aliases": "ns-resize n-resize s-resize row-resize top_side bottom_side v_double_arrow sb_v_double_arrow size_ver"
  }
}
```

Nama file harus sama persis dengan nama `.ani`.

Jalankan kembali:

```bash
python ani_to_hyprcursor.py ~/Downloads/MyCursor
```

Mapping ini hanya diperlukan untuk nama cursor yang tidak bisa ditebak dengan
baik oleh deteksi otomatis.

## Ganti cursor kapan saja

Misalnya sudah punya:

```text
Furina 2.0
Bibata
MyCursor
```

Tidak perlu menjalankan converter lagi.

Cukup:

```bash
hyprctl setcursor "Bibata" 32
```

atau:

```bash
hyprctl setcursor "Furina 2.0" 32
```

Untuk mengganti ukuran:

```bash
hyprctl setcursor "Furina 2.0" 48
```

Untuk penggunaan permanen, set:

```lua
cursor = {
    enable_hyprcursor = true,
},

hl.env("HYPRCURSOR_THEME", "Furina 2.0")
hl.env("HYPRCURSOR_SIZE", "32")
```

Jika menggunakan konfigurasi Hyprland biasa:

```ini
env = HYPRCURSOR_THEME,Furina 2.0
env = HYPRCURSOR_SIZE,32
```

## Ganti ke cursor lain tanpa menghapus Furina

Ini aman:

```bash
hyprctl setcursor "MyCursor" 32
```

Theme Furina tetap tersimpan.

Untuk kembali:

```bash
hyprctl setcursor "Furina 2.0" 32
```

## Jika ingin menghapus theme

Hapus hanya folder theme yang ingin dihapus:

```bash
rm -rf ~/.local/share/icons/"MyCursor"
```

Jangan menghapus seluruh:

```text
~/.local/share/icons
```

karena folder tersebut dapat berisi theme/icon lain.

## Catatan kompatibilitas aplikasi

Hyprcursor bekerja langsung pada Hyprland dan aplikasi yang mendukung
server-side cursors. Beberapa aplikasi yang belum mendukung Hyprcursor masih
dapat menggunakan XCursor sebagai fallback. Hyprland mendokumentasikan GTK
sebagai salah satu contoh aplikasi yang dapat membutuhkan XCursor/GSettings
untuk sinkronisasi cursor. [Hyprland Wiki](https://wiki.hypr.land/hypr-ecosystem/user/hyprcursor/)

Jadi converter ini sengaja menghasilkan **Hyprcursor native**, bukan kumpulan
symlink XCursor.

## Cara paling singkat

```bash
sudo pacman -S python-pillow hyprcursor

python ani_to_hyprcursor.py ~/Downloads/NamaCursor

hyprctl setcursor "NamaCursor" 32
```

Selesai.

---

### Sumber

- Hyprcursor theme format dan `define_override` / `define_size`:
  https://github.com/hyprwm/hyprcursor/blob/main/docs/MAKING_THEMES.md
- `hyprcursor-util`:
  https://github.com/hyprwm/hyprcursor/blob/main/hyprcursor-util/README.md
- Hyprland cursor configuration:
  https://wiki.hypr.land/hypr-ecosystem/user/hyprcursor/

## Uninstalling a converted cursor theme

The converter installs the generated Hyprcursor theme under:

```text
~/.local/share/icons/<Theme Name>/
```

To remove a cursor theme, first switch to another theme:

```bash
hyprctl setcursor "Adwaita" 32
```

Then remove the generated theme directory. For example:

```bash
rm -rf ~/.local/share/icons/"Skirk Cursor"
```

For Furina:

```bash
rm -rf ~/.local/share/icons/"Furina 2.0"
```

Replace the name with the exact theme directory you want to remove.

### Check installed custom themes

Before deleting anything, you can list your local themes:

```bash
find ~/.local/share/icons -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort
```

**Important:** only remove directories that you know were generated/installed by this converter. Do not delete system themes under `/usr/share/icons/`.

If the theme is currently active, switch to another cursor theme before removing it. After removing a theme, no reboot is normally required.

