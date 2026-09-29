#!/usr/bin/env python3
"""
Generic Windows .ANI -> native Hyprcursor converter.

Usage:
    python ani_to_hyprcursor.py
    python ani_to_hyprcursor.py /path/to/ani-folder
    python ani_to_hyprcursor.py /path/to/ani-folder --theme "My Cursor"

The converter:
- accepts any number of .ani files
- automatically guesses standard cursor roles from filenames
- preserves ANI animation timing/order
- creates native Hyprcursor themes
- generates multiple predefined sizes
- lets Hyprcursor scale sizes between the predefined variants
- creates standard Hyprland resize aliases automatically
- never edits the live theme until the whole build succeeds

Optional cursor-map.json in the source directory can override the automatic
name/alias detection. See README.md.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow belum terpasang.")
    print("Install: sudo pacman -S python-pillow")
    raise SystemExit(1)


# Generic role detection. These are cursor-role names, not theme-specific names.
ROLE_ALIASES = {
    "normal": ("left_ptr", "arrow default top_left_arrow dnd-none X_cursor"),
    "default": ("left_ptr", "arrow default top_left_arrow dnd-none X_cursor"),
    "arrow": ("left_ptr", "arrow default top_left_arrow dnd-none X_cursor"),
    "alt": ("right_ptr", "right_ptr"),
    "busy": ("watch", "watch wait left_ptr_watch"),
    "wait": ("watch", "watch wait left_ptr_watch"),
    "work": ("progress", "progress"),
    "progress": ("progress", "progress"),
    "hand": ("hand2", "hand2 hand pointer pointing_hand openhand grab grabbing"),
    "pointer": ("pointer", "pointer link pointing_hand"),
    "link": ("pointer", "pointer link pointing_hand"),
    "help": ("help", "help question_arrow left_ptr_help whats_this"),
    "text": ("text", "text ibeam xterm"),
    "ibeam": ("text", "text ibeam xterm"),
    "move": ("move", "move fleur size_all all-scroll"),
    "fleur": ("move", "move fleur size_all all-scroll"),
    "location": ("crosshair", "crosshair cross tcross"),
    "crosshair": ("crosshair", "crosshair cross tcross"),
    "precision": ("tcross", "tcross"),
    "unavailable": ("not-allowed", "not-allowed forbidden no-drop crossed_circle circle"),
    "forbidden": ("not-allowed", "not-allowed forbidden no-drop crossed_circle circle"),
    "dgn1": (
        "nwse-resize",
        "nwse-resize nw-resize se-resize size_fdiag fd_double_arrow "
        "top_left_corner bottom_right_corner",
    ),
    "dgn2": (
        "nesw-resize",
        "nesw-resize ne-resize sw-resize size_bdiag bd_double_arrow "
        "top_right_corner bottom_left_corner",
    ),
    "horz": (
        "ew-resize",
        "ew-resize e-resize w-resize col-resize left_side right_side "
        "h_double_arrow sb_h_double_arrow size_hor split_h",
    ),
    "horizontal": (
        "ew-resize",
        "ew-resize e-resize w-resize col-resize left_side right_side "
        "h_double_arrow sb_h_double_arrow size_hor split_h",
    ),
    "vert": (
        "ns-resize",
        "ns-resize n-resize s-resize row-resize top_side bottom_side "
        "v_double_arrow sb_v_double_arrow size_ver split_v",
    ),
    "vertical": (
        "ns-resize",
        "ns-resize n-resize s-resize row-resize top_side bottom_side "
        "v_double_arrow sb_v_double_arrow size_ver split_v",
    ),
}


def clean_stem(path: Path) -> str:
    s = path.stem.lower()
    s = re.sub(r"^(furina|cursor|cursors)[\s._-]+", "", s)
    s = re.sub(r"[\s._-]+", " ", s).strip()
    return s


def detect_role(path: Path) -> tuple[str, str]:
    """Return canonical Hyprcursor name + standard aliases."""
    s = clean_stem(path)

    # Longest / most specific patterns first.
    patterns = [
        ("dgn1", "dgn1"), ("dgn2", "dgn2"),
        ("nwse resize", "dgn1"), ("nwse", "dgn1"),
        ("nesw resize", "dgn2"), ("nesw", "dgn2"),
        ("horizontal", "horizontal"), ("horz", "horz"),
        ("vertical", "vertical"), ("vert", "vert"),
        ("crosshair", "crosshair"), ("precision", "precision"),
        ("unavailable", "unavailable"), ("forbidden", "forbidden"),
        ("not allowed", "unavailable"),
        ("right ptr", "alt"), ("alt", "alt"),
        ("left ptr", "normal"), ("normal", "normal"),
        ("default", "default"), ("arrow", "arrow"),
        ("busy", "busy"), ("wait", "wait"), ("work", "work"),
        ("progress", "progress"),
        ("hand", "hand"), ("grab", "hand"),
        ("link", "link"), ("pointer", "pointer"),
        ("help", "help"), ("question", "help"),
        ("text", "text"), ("ibeam", "ibeam"),
        ("move", "move"), ("fleur", "fleur"),
        ("location", "location"),
    ]

    for needle, role in patterns:
        if needle in s:
            return ROLE_ALIASES[role]

    # Unknown cursor: use a safe filename-derived shape name.
    name = re.sub(r"[^a-z0-9_-]+", "-", s).strip("-") or "cursor"
    return name, name


def load_map(source: Path) -> dict[str, dict]:
    path = source / "cursor-map.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"cursor-map.json tidak valid: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("cursor-map.json harus berupa object JSON.")
    return data


def mapping_for(path: Path, overrides: dict[str, dict]) -> tuple[str, str]:
    if path.name in overrides:
        item = overrides[path.name]
        if not isinstance(item, dict):
            raise RuntimeError(f"Mapping untuk {path.name} harus object.")
        name = str(item.get("name", "")).strip()
        aliases = str(item.get("aliases", "")).strip()
        if not name:
            raise RuntimeError(f"Mapping {path.name} tidak punya 'name'.")
        return name, aliases or name
    return detect_role(path)


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def parse_chunks(data: bytes, start: int, end: int):
    p = start
    while p + 8 <= end:
        tag = data[p:p + 4]
        size = u32(data, p + 4)
        a = p + 8
        b = min(a + size, end)
        yield tag, a, b
        p = a + size + (size & 1)


def find_fram_lists(data: bytes):
    result = []

    def walk(start: int, end: int):
        p = start
        while p + 8 <= end:
            tag = data[p:p + 4]
            size = u32(data, p + 4)
            a = p + 8
            b = min(a + size, end)

            if tag == b"LIST" and a + 4 <= b:
                kind = data[a:a + 4]
                if kind == b"fram":
                    result.append((a + 4, b))
                walk(a + 4, b)

            p = a + size + (size & 1)

    walk(12, len(data))
    return result


def extract_frames(data: bytes) -> list[bytes]:
    if not data.startswith(b"RIFF") or data[8:12] != b"ACON":
        raise ValueError("bukan Windows ANI")

    frames = []
    regions = find_fram_lists(data) or [(12, len(data))]

    for start, end in regions:
        for tag, a, b in parse_chunks(data, start, end):
            if tag in (b"icon", b"ICON", b"cur ", b"CUR "):
                frames.append(data[a:b])

    if not frames:
        raise ValueError("frame CUR/ICON tidak ditemukan")
    return frames


def ani_rate_and_sequence(data: bytes, count: int):
    rates = []
    seq = []

    for tag, a, b in parse_chunks(data, 12, len(data)):
        payload = data[a:b]
        if tag == b"rate":
            rates = [u32(payload, i) for i in range(0, len(payload) - 3, 4)]
        elif tag == b"seq ":
            seq = [u32(payload, i) for i in range(0, len(payload) - 3, 4)]

    if not rates:
        rates = [6] * count
    if len(rates) < count:
        rates += [rates[-1]] * (count - len(rates))

    seq = [x for x in seq if x < count] if seq else list(range(count))
    return rates, seq


def remove_edge_black(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    amin, amax = alpha.getextrema()

    if amin != 255 or amax != 255:
        return img

    px = img.load()
    w, h = img.size
    q = deque()
    seen = set()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))

        r, g, b, a = px[x, y]
        if a == 255 and r <= 8 and g <= 8 and b <= 8:
            px[x, y] = (r, g, b, 0)
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return img


def decode_cur(cur: bytes):
    with Image.open(io.BytesIO(cur)) as im:
        hotspot = getattr(im, "hotspot", None)
        if hotspot is None:
            hotspot = im.info.get("hotspot", (0, 0))
        if not hotspot or len(hotspot) != 2:
            hotspot = (0, 0)

        img = remove_edge_black(im.copy())
        return img, int(hotspot[0]), int(hotspot[1])


def write_cursor(
    ani: Path,
    name: str,
    aliases: str,
    root: Path,
    sizes: tuple[int, ...],
):
    data = ani.read_bytes()
    frames = extract_frames(data)
    rates, sequence = ani_rate_and_sequence(data, len(frames))
    decoded = [decode_cur(f) for f in frames]

    cursor_dir = root / name
    cursor_dir.mkdir(parents=True, exist_ok=True)

    first_img, first_hx, first_hy = decoded[0]
    base = max(first_img.width, first_img.height)
    hotspot_x = first_hx / base if base else 0.5
    hotspot_y = first_hy / base if base else 0.5

    lines = [
        "resize_algorithm = bilinear",
        f"hotspot_x = {hotspot_x:.8f}",
        f"hotspot_y = {hotspot_y:.8f}",
    ]

    for alias in aliases.split():
        lines.append(f"define_override = {alias}")

    for size in sizes:
        for frame_no, seq_index in enumerate(sequence):
            img, _, _ = decoded[seq_index]
            out = img.resize((size, size), Image.Resampling.LANCZOS)
            png = cursor_dir / f"image{size}_{frame_no:04d}.png"
            out.save(png, optimize=True)

            rate = rates[seq_index] if seq_index < len(rates) else 6
            delay_ms = max(1, round(rate * 1000 / 60))
            lines.append(f"define_size = {size}, {png.name}, {delay_ms}")

    (cursor_dir / "meta.hl").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return len(frames), len(sequence)


def write_manifest(root: Path, theme: str):
    # The temporary theme directory may not exist yet.
    # Create it before writing manifest.hl.
    root.mkdir(parents=True, exist_ok=True)

    (root / "manifest.hl").write_text(
        f"name = {theme}\n"
        f"description = {theme} animated Hyprcursor theme\n"
        "version = 1.0\n"
        "cursors_directory = hyprcursors\n",
        encoding="utf-8",
    )


def parse_sizes(value: str) -> tuple[int, ...]:
    sizes = tuple(sorted({int(x.strip()) for x in value.split(",") if x.strip()}))
    if not sizes or any(x <= 0 for x in sizes):
        raise argparse.ArgumentTypeError("sizes harus berisi angka positif.")
    return sizes


def main():
    parser = argparse.ArgumentParser(
        description="Convert generic Windows .ANI cursor packs to Hyprcursor."
    )
    parser.add_argument(
        "source", nargs="?", default=".",
        help="folder yang berisi file .ani (default: folder saat ini)",
    )
    parser.add_argument(
        "--theme", default=None,
        help="nama theme; default = nama folder source",
    )
    parser.add_argument(
        "--sizes", type=parse_sizes,
        default=(12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64),
        help="ukuran PNG, contoh: 16,24,32,48,64",
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"Folder tidak ditemukan: {source}")

    theme = args.theme or source.name
    ani_files = sorted(source.glob("*.ani"), key=lambda p: p.name.lower())

    if not ani_files:
        raise SystemExit(f"Tidak ada file .ani di: {source}")

    if shutil.which("hyprcursor-util") is None:
        print("hyprcursor-util belum ditemukan.")
        print("Install: sudo pacman -S hyprcursor")
        raise SystemExit(1)

    mapping = load_map(source)

    # Detect duplicate canonical names before doing any work.
    # Some cursor packs contain both files such as pointer.ani and link.ani.
    # They may intentionally map to the same standard Hyprcursor shape.
    # Keep the first standard mapping and automatically give later duplicates
    # a unique filename-derived shape name, so generic packs do not require
    # manual cursor-map.json edits just to compile.
    planned = []
    used = set()

    for ani in ani_files:
        detected_name, aliases = mapping_for(ani, mapping)
        name = detected_name

        if name in used:
            stem = re.sub(
                r"[^a-z0-9_-]+", "-", ani.stem.lower()
            ).strip("-") or "cursor"

            name = stem
            suffix = 2
            while name in used:
                name = f"{stem}-{suffix}"
                suffix += 1

            # The standard aliases are already owned by the first mapping.
            # Do not create duplicate define_override entries.
            aliases = ""

            print(
                f"[INFO] {ani.name}: '{detected_name}' bentrok, "
                f"menggunakan nama unik '{name}'"
            )

        used.add(name)
        planned.append((ani, name, aliases))

    out = Path.home() / ".local" / "share" / "icons" / theme
    build_root = Path(tempfile.mkdtemp(prefix="ani-hyprcursor-"))
    working = build_root / theme
    working_hypr = working / "hyprcursors"
    compiled_parent = build_root / "compiled"

    print(f"Source : {source}")
    print(f"Theme  : {theme}")
    print(f"ANI    : {len(ani_files)} file")
    print(f"Sizes  : {', '.join(map(str, args.sizes))} px")
    print()

    try:
        write_manifest(working, theme)
        working_hypr.mkdir(parents=True, exist_ok=True)

        ok = 0
        for ani, name, aliases in planned:
            try:
                frames, sequence = write_cursor(
                    ani, name, aliases, working_hypr, args.sizes
                )
                print(
                    f"[OK] {ani.name} -> {name} "
                    f"({frames} frame, {sequence} animasi)"
                )
                ok += 1
            except Exception as exc:
                print(f"[FAIL] {ani.name}: {exc}")
                raise

        print()
        print("Mengompilasi Hyprcursor...")
        compiled_parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "hyprcursor-util",
                "--create", str(working),
                "--output", str(compiled_parent),
            ],
            check=True,
        )

        candidates = [x for x in compiled_parent.iterdir() if x.is_dir()]
        if len(candidates) != 1:
            raise RuntimeError(
                "Output hyprcursor-util tidak ditemukan dengan jelas."
            )
        compiled = candidates[0]

        backup = out.with_name(out.name + " backup-before-hyprcursor")
        if out.exists():
            if backup.exists():
                shutil.rmtree(backup)
            out.rename(backup)

        shutil.move(str(compiled), str(out))

        print()
        print(f"BERHASIL {ok}/{len(ani_files)}")
        print(f"Theme  : {out}")
        if out.with_name(out.name + " backup-before-hyprcursor").exists():
            print(f"Backup : {backup}")
        print()
        print(f'hyprctl setcursor "{theme}" 32')

    finally:
        shutil.rmtree(build_root, ignore_errors=True)


if __name__ == "__main__":
    main()
