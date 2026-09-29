# ANI to Hyprcursor Converter

> Indonesian documentation: see [README.id.md](README.id.md).

Convert animated Windows cursor `.ani` files into native **Hyprcursor themes** for Hyprland.

The converter is designed to be generic: it is not hardcoded for Furina, Skirk, or any other specific cursor pack.

## Features

- Converts `.ani` cursor files to native Hyprcursor format.
- Preserves cursor animation and frame timing.
- Automatically maps common cursor names to standard Hyprcursor shapes.
- Handles duplicate/colliding cursor names automatically.
- Generates multiple cursor sizes from **12 px through 64 px**.
- Creates resize-related aliases such as `left_side`, `right_side`, `top_side`, and corner shapes.
- Creates a theme that can be loaded with `hyprctl setcursor`.
- Creates a backup when replacing an existing generated theme.

## Requirements

Arch Linux packages:

```bash
sudo pacman -S python-pillow hyprcursor
```

Python 3 is required.

## Installation / Usage

Put the converter script somewhere convenient:

```bash
mkdir -p ~/.local/bin
cp ani_to_hyprcursor.py ~/.local/bin/
chmod +x ~/.local/bin/ani_to_hyprcursor.py
```

Go to a folder containing your `.ani` files, or pass the folder as an argument:

```bash
python3 ~/.local/bin/ani_to_hyprcursor.py "/path/to/Cursor Pack"
```

If no source directory is given, run the script from the cursor-pack directory:

```bash
python3 ani_to_hyprcursor.py
```

The generated theme is installed under:

```text
~/.local/share/icons/<Theme Name>/
```

Then activate it:

```bash
hyprctl setcursor "Theme Name" 32
```

Change `32` to any generated size from 12 through 64.

## Changing Cursor Themes

You do not need to reinstall the converter to change themes.

Example:

```bash
hyprctl setcursor "Furina 2.0" 32
```

Then switch to another theme:

```bash
hyprctl setcursor "Skirk Cursor" 48
```

The theme name must match the installed theme name.

## Hyprland Configuration

For native Hyprcursor support, use:

```lua
cursor = {
    enable_hyprcursor = true,
}
```

Set the environment variables in your Hyprland Lua configuration:

```lua
hl.env("HYPRCURSOR_THEME", "Furina 2.0")
hl.env("HYPRCURSOR_SIZE", "32")
```

After changing the configuration, restart/reload Hyprland as appropriate.

## Uninstalling a Converted Cursor Theme

First switch to another cursor theme:

```bash
hyprctl setcursor "Adwaita" 32
```

Then remove the generated theme directory.

Example:

```bash
rm -rf ~/.local/share/icons/"Skirk Cursor"
```

Or:

```bash
rm -rf ~/.local/share/icons/"Furina 2.0"
```

List local themes before deleting if you are unsure:

```bash
find ~/.local/share/icons -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort
```

Only remove themes you recognize as custom/generated themes. Do **not** remove system themes from `/usr/share/icons/`.

A reboot is normally not required after uninstalling a theme.

## Duplicate Cursor Names

Some `.ani` packs contain multiple files that map to the same standard cursor shape.

For example:

```text
Skirk link.ani
Skirk normal.ani
```

may both initially map to an existing standard shape.

The converter automatically keeps the first standard mapping and assigns a unique name to later collisions, for example:

```text
[INFO] Skirk link.ani: 'pointer' bentrok, using unique name 'skirk-link'
```

This does not require manual editing of `cursor-map.json` for ordinary collisions.

## Output

The converter reports:

- source directory
- theme name
- number of `.ani` files
- generated sizes
- conversion progress
- backup location
- final success/failure count

If conversion succeeds, activate the generated theme with:

```bash
hyprctl setcursor "Theme Name" 32
```

## Troubleshooting

### The cursor does not change immediately

Run:

```bash
hyprctl setcursor "Theme Name" 32
```

Make sure the theme name is exact.

### A cursor shape is missing

The converter maps common `.ani` names automatically. Unusual cursor-pack names may need a custom mapping using `cursor-map.json`.

### Hyprland still uses another cursor

Check:

```bash
hyprctl getoption cursor:enable_hyprcursor
```

For native Hyprcursor themes, it should report:

```text
bool: true
```

Also make sure your `HYPRCURSOR_THEME` and `HYPRCURSOR_SIZE` values are correct.

## Notes

This converter is intended for `.ani` cursor packs and native Hyprcursor on Hyprland. Applications that do not use Hyprcursor may use their own cursor handling or an XCursor fallback.
