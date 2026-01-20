# Supaplex DAT → PNG extractor

A tiny utility to convert the Supaplex `.DAT` graphics files into viewable PNGs using the same bitplane decoding the original game uses.

## Requirements
- Python 3.9+
- Pillow (`pip install pillow`)

## Usage
Basic examples:
- `python sp_extract_dat_png.py --dat-dir ../resources --output-dir ./out`
- `python sp_extract_dat_png.py --files MENU.DAT TITLE.DAT --palette-file ../resources/PALETTES.DAT`

Notes:
- If `PALETTES.DAT` is available (auto-detected under `--dat-dir` or passed with `--palette-file`), the game palettes are used. Otherwise a grayscale fallback is applied, except for the built-in TITLE/TITLE1/TITLE2 palettes.
- Known files are listed in `DAT_SPECS` inside the script (MENU, BACK, CONTROLS, GFX, TITLE*, PANEL, MOVING, FIXED, CHARS6/8). Unknown `.DAT` files are skipped.

## Output previews

The images resulting from running this tool against Supaplex Spfix63 build are located in the [/out](/out) directory. Previews below:

### TITLE.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/title.png"  width="960px">

### MOVING.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/moving.png" width="960">

### FIXED.DAT
<img src="https://img.visualrealmsoftware.com/scale/1280/github.com/visrealm/supaplex-tools/raw/main/out/fixed.png" width="1280">

### TITLE1.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/title1.png" width="960">

### TITLE2.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/title2.png" width="960">

### MENU.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/menu.png" width="960">

### PANEL.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/panel.png" width="960">

### CHARS6.DAT
<img src="https://img.visualrealmsoftware.com/scale/1024/github.com/visrealm/supaplex-tools/raw/main/out/chars6.png" width="1024">

### CHARS8.DAT
<img src="https://img.visualrealmsoftware.com/scale/1024/github.com/visrealm/supaplex-tools/raw/main/out/chars8.png" width="1024">

### CONTROLS.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/controls.png" width="960">

### GFX.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/gfx.png" width="960">

### BACK.DAT
<img src="https://img.visualrealmsoftware.com/scale/960/github.com/visrealm/supaplex-tools/raw/main/out/back.png" width="960">

## License
This code is licensed under the MIT license. See [LICENSE](LICENSE).
