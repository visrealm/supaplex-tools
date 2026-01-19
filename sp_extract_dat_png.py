"""
Extract Supaplex .DAT graphics into PNG files. License: MIT.

github.com/visrealm/supaplex-tools

Copyright (c) 2026 Troy Schrapel (visrealm)

-------------------------------------------------------------------------------

The bitmaps are stored as four bitplanes (B, G, R, intensity) laid out per row:
40 bytes per plane for a 320-pixel-wide image (width / 8 bytes per plane).
The final palette index for one pixel is built as:
 (b << 0) | (g << 1) | (r << 2) | (i << 3).

Usage examples
--------------
python sp_extract_dat_png.py --dat-dir <sp63path>/resources --output-dir ./out
python sp_extract_dat_png.py --files MENU.DAT TITLE.DAT --palette-file <sp63path>/resources/PALETTES.DAT

The script will try to use palettes from PALETTES.DAT (4 palettes), or the
built-in title palettes for TITLE*.DAT. If a palette is not available, a
fallback grayscale palette is used so the PNG still renders visibly.


"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image

# ---------- Palette helpers -------------------------------------------------

Color = Tuple[int, int, int]
Palette = List[Color]

# Values copied from gTitlePaletteData, gTitle1PaletteData and gTitle2PaletteData
_TITLE_PALETTE_RAW = [
    0x02, 0x03, 0x05, 0x00, 0x0D, 0x0A, 0x04, 0x0C, 0x02, 0x06, 0x06, 0x02, 0x03, 0x09, 0x09, 0x03,
    0x0B, 0x08, 0x03, 0x06, 0x02, 0x07, 0x07, 0x0A, 0x08, 0x06, 0x0D, 0x09, 0x06, 0x04, 0x0B, 0x01,
    0x09, 0x01, 0x00, 0x04, 0x0B, 0x01, 0x00, 0x04, 0x0D, 0x01, 0x00, 0x0C, 0x0F, 0x01, 0x00, 0x0C,
    0x0F, 0x06, 0x04, 0x0C, 0x02, 0x05, 0x06, 0x08, 0x0F, 0x0C, 0x06, 0x0E, 0x0C, 0x0C, 0x0D, 0x0E,
]

_TITLE1_PALETTE_RAW = [
    0x00, 0x00, 0x00, 0x00, 0x0F, 0x0F, 0x0F, 0x0F, 0x08, 0x08, 0x08, 0x08, 0x0A, 0x0A, 0x0A, 0x07,
    0x0A, 0x0A, 0x0A, 0x07, 0x0B, 0x0B, 0x0B, 0x07, 0x0E, 0x01, 0x01, 0x04, 0x09, 0x09, 0x09, 0x07,
    0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x09, 0x00, 0x00, 0x04, 0x0B, 0x00, 0x00, 0x0C,
    0x08, 0x08, 0x08, 0x08, 0x05, 0x05, 0x05, 0x08, 0x06, 0x06, 0x06, 0x08, 0x08, 0x08, 0x08, 0x08,
]

_TITLE2_PALETTE_RAW = [
    0x00, 0x00, 0x00, 0x00, 0x0F, 0x0F, 0x0F, 0x0F, 0x06, 0x06, 0x06, 0x08, 0x0A, 0x0A, 0x0A, 0x07,
    0x0A, 0x0A, 0x0A, 0x07, 0x0B, 0x0B, 0x0B, 0x07, 0x0E, 0x01, 0x01, 0x04, 0x09, 0x09, 0x09, 0x07,
    0x01, 0x03, 0x07, 0x00, 0x08, 0x08, 0x08, 0x08, 0x09, 0x00, 0x00, 0x04, 0x0B, 0x00, 0x00, 0x0C,
    0x00, 0x02, 0x0A, 0x01, 0x05, 0x05, 0x05, 0x08, 0x06, 0x06, 0x06, 0x08, 0x08, 0x08, 0x08, 0x07,
]


def _convert_palette_data_to_palette(raw: Sequence[int]) -> Palette:
    if len(raw) != 64:
        raise ValueError(f"Palette data must have 64 bytes, got {len(raw)}")
    palette: Palette = []
    for i in range(16):
        r = raw[i * 4 + 0] << 4
        g = raw[i * 4 + 1] << 4
        b = raw[i * 4 + 2] << 4
        palette.append((r, g, b))
    return palette


def load_palettes_file(path: Path) -> List[Palette]:
    data = path.read_bytes()
    if len(data) % 64 != 0:
        raise ValueError(f"PALETTES.DAT size {len(data)} is not a multiple of 64 bytes")
    palettes: List[Palette] = []
    for offset in range(0, len(data), 64):
        palettes.append(_convert_palette_data_to_palette(data[offset : offset + 64]))
    return palettes


def build_png_palette(palette: Palette) -> List[int]:
    """Expand a 16-color palette to Pillow's 256-entry palette table."""
    entries: List[int] = []
    for r, g, b in palette:
        entries.extend([r, g, b])
    # Repeat the last color to fill 256 entries (Pillow requires 768 values).
    last = palette[-1]
    while len(entries) < 256 * 3:
        entries.extend([last[0], last[1], last[2]])
    return entries


def grayscale_palette() -> Palette:
    return [(i * 17, i * 17, i * 17) for i in range(16)]


# ---------- Decoding helpers -----------------------------------------------

def decode_bitplane4(data: bytes, width: int, height: int) -> bytearray:
    expected_size = width * height // 2
    if len(data) < expected_size:
        raise ValueError(f"Unexpected data size {len(data)} < expected {expected_size}")

    row_bytes = width // 8
    stride = row_bytes * 4
    pixels = bytearray(width * height)

    for y in range(height):
        base = y * stride
        for x in range(width):
            byte_idx = x // 8
            bit = 7 - (x % 8)
            b = (data[base + byte_idx] >> bit) & 0x1
            g = (data[base + row_bytes + byte_idx] >> bit) & 0x1
            r = (data[base + 2 * row_bytes + byte_idx] >> bit) & 0x1
            i = (data[base + 3 * row_bytes + byte_idx] >> bit) & 0x1
            pixels[y * width + x] = (b) | (g << 1) | (r << 2) | (i << 3)
    return pixels


def decode_font_1bit(data: bytes, width: int, height: int) -> bytearray:
    expected_size = width * height // 8
    if len(data) < expected_size:
        raise ValueError(f"Unexpected font data size {len(data)} < expected {expected_size}")

    row_bytes = width // 8
    pixels = bytearray(width * height)
    for y in range(height):
        base = y * row_bytes
        for x in range(width):
            byte_idx = x // 8
            bit = 7 - (x % 8)
            value = (data[base + byte_idx] >> bit) & 0x1
            pixels[y * width + x] = 255 * value
    return pixels


# ---------- Known DAT files -------------------------------------------------

DatSpec = Dict[str, object]

DAT_SPECS: Dict[str, DatSpec] = {
    "MENU.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("palettes", 1)},
    "CONTROLS.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("palettes", 2)},
    "BACK.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("palettes", 1)},
    "GFX.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("palettes", 1)},
    "TITLE.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("title", None)},
    "TITLE1.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("title1", None)},
    "TITLE2.DAT": {"width": 320, "height": 200, "decoder": "bitplane4", "palette": ("title2", None)},
    "PANEL.DAT": {"width": 320, "height": 24, "decoder": "bitplane4", "palette": ("palettes", 1)},
    "MOVING.DAT": {"width": 320, "height": 462, "decoder": "bitplane4", "palette": ("palettes", 1)},
    "FIXED.DAT": {"width": 640, "height": 16, "decoder": "bitplane4", "palette": ("palettes", 1)},
    # Fonts are single-bit bitmaps, 512x8 pixels each.
    "CHARS6.DAT": {"width": 512, "height": 8, "decoder": "font1bit", "palette": None},
    "CHARS8.DAT": {"width": 512, "height": 8, "decoder": "font1bit", "palette": None},
}


def pick_palette(spec: DatSpec, palettes_file: Optional[List[Palette]]) -> Palette:
    palette_info = spec.get("palette")
    if palette_info is None:
        return grayscale_palette()

    palette_type, index = palette_info  # type: ignore[misc]
    if palette_type == "title":
        return _convert_palette_data_to_palette(_TITLE_PALETTE_RAW)
    if palette_type == "title1":
        return _convert_palette_data_to_palette(_TITLE1_PALETTE_RAW)
    if palette_type == "title2":
        return _convert_palette_data_to_palette(_TITLE2_PALETTE_RAW)

    if palette_type == "palettes":
        if palettes_file is None:
            return grayscale_palette()
        if index is None:
            index = 0
        if index >= len(palettes_file):
            return grayscale_palette()
        return palettes_file[index]

    return grayscale_palette()


# ---------- Main workflow ---------------------------------------------------


def decode_and_save(dat_path: Path, out_path: Path, palettes_file: Optional[List[Palette]]) -> None:
    spec = DAT_SPECS.get(dat_path.name.upper())
    if spec is None:
        raise KeyError(f"Unknown DAT file: {dat_path.name}")

    width = int(spec["width"])
    height = int(spec["height"])
    decoder = spec["decoder"]
    data = dat_path.read_bytes()

    if decoder == "bitplane4":
        pixels = decode_bitplane4(data, width, height)
        palette = pick_palette(spec, palettes_file)
        img = Image.frombytes("P", (width, height), bytes(pixels))
        img.putpalette(build_png_palette(palette))
    elif decoder == "font1bit":
        pixels = decode_font_1bit(data, width, height)
        img = Image.frombytes("L", (width, height), bytes(pixels))
    else:
        raise ValueError(f"Unsupported decoder: {decoder}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Supaplex DAT graphics into PNG files.")
    parser.add_argument("--dat-dir", type=Path, default=Path.cwd(), help="Directory containing the .DAT files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dat_png"),
        help="Destination directory for the PNG files.",
    )
    parser.add_argument(
        "--palette-file",
        type=Path,
        default=None,
        help="Path to PALETTES.DAT. If not provided, falls back to grayscale except for title palettes.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Specific DAT files to extract. Defaults to all known DAT specs present in dat-dir.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    dat_dir: Path = args.dat_dir
    output_dir: Path = args.output_dir

    selected_files: Iterable[str]
    if args.files:
        selected_files = [name.upper() for name in args.files]
    else:
        selected_files = DAT_SPECS.keys()

    palettes_from_file: Optional[List[Palette]] = None
    if args.palette_file is not None:
        if not args.palette_file.exists():
            print(f"Palette file not found: {args.palette_file}", file=sys.stderr)
            return 1
        palettes_from_file = load_palettes_file(args.palette_file)
    else:
        # Try to auto-locate PALETTES.DAT under dat-dir.
        palettes_candidate = dat_dir / "PALETTES.DAT"
        if palettes_candidate.exists():
            palettes_from_file = load_palettes_file(palettes_candidate)

    processed = 0
    for name in selected_files:
        spec = DAT_SPECS.get(name)
        if spec is None:
            print(f"Skipping unknown DAT file: {name}")
            continue
        dat_path = dat_dir / name
        if not dat_path.exists():
            print(f"Missing {dat_path}, skipping")
            continue
        out_name = name.replace(".DAT", ".png").lower()
        out_path = output_dir / out_name
        try:
            decode_and_save(dat_path, out_path, palettes_from_file)
            print(f"Wrote {out_path}")
            processed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to convert {name}: {exc}", file=sys.stderr)
    if processed == 0:
        print("No files converted", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
