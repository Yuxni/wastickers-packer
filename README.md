# whatsappsticker

Convert sticker images into `.wastickers` files — the format used by WhatsApp sticker maker apps.

Transfer the `.wastickers` file to your phone and open it with **Sticker Maker Studio** (iOS) or **WAStickerApps** (Android) to install directly into WhatsApp.

## Quick start

```bash
pip install .
whatsappsticker /path/to/stickers -o ./packs
```

Scans the folder for images, converts each to 512×512 WebP (≤100 KB), groups them into packs of up to 30, and produces `.wastickers` ZIP files.

## Installation

Requires **Python 3.8+** and **Pillow**.

```bash
pip install .
```

For development:

```bash
pip install -e .[dev]
pytest
```

## Usage

### Flat folder — all images become one pack

```
whatsappsticker path/to/stickers -o ./packs
```

Each pack name is derived from the folder name. Use `--name` to override:

```
whatsappsticker path/to/stickers -o ./packs --name "My Pack"
```

### Subfolder mode — each subfolder is a separate pack

```
stickers/
├── animals/       → "Animals" pack
│   ├── cat.webp
│   └── dog.webp
├── food/          → "Food" pack
│   ├── pizza.png
│   └── taco.jpg
└── reactions/     → "Reactions" pack
    ├── hug.webp
    └── wave.webp
```

```
whatsappsticker stickers/ -o ./packs
```

Each subfolder must contain **3–30 images**. Flat mode can exceed 30 — packs are split automatically.

### Generate HTML preview

```
whatsappsticker path/to/stickers -o ./packs --report
```

Creates `index.html` with a mobile-friendly gallery of all packs, including tray icons and sticker previews.

### Custom publisher name

```
whatsappsticker path/to/stickers -o ./packs --publisher "Your Name"
```

## Output

```
packs/
├── animals.wastickers          ← open on phone to install
├── food.wastickers
├── reactions.wastickers
├── index.html                  ← preview page (with --report)
├── animals/
│   ├── tray.png
│   ├── sticker_01.webp
│   └── ...
├── food/
│   ├── tray.png
│   └── ...
└── reactions/
    └── ...
```

## Options

| Flag                    | Default                    | Description                            |
|-------------------------|----------------------------|----------------------------------------|
| `-o, --output`          | `output/`                  | Output directory                       |
| `--name`                | folder name (title-cased)  | Pack name for flat folders             |
| `--publisher`           | `WhatsApp Sticker Tool`    | Publisher name in metadata             |
| `--report`              | `False`                    | Generate HTML preview page with gallery|

## Install on your phone

1. Transfer the `.wastickers` file to your phone (AirDrop / iCloud / Files on iOS, USB / cloud on Android)
2. Open the file with **Sticker Maker Studio** (iOS) or **WAStickerApps** (Android)
3. Tap "Add to WhatsApp"

## How it works

1. **Scan** — finds all image files (`.webp`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`) in the input
2. **Group** — organises images into packs. Subfolders = named packs; flat folder = single pack (split at 30)
3. **Convert** — resizes each image to 512×512 WebP (≤100 KB), creates a 96×96 PNG tray icon from the first image
4. **Package** — bundles everything into a `.wastickers` ZIP with `author.txt`, `title.txt`, `tray.png`, and numbered stickers

## API

The package can also be used programmatically:

```python
from pathlib import Path
from whatsappsticker.grouping import plan_packs
from whatsappsticker.wastickers import create_pack, pack_to_wastickers

# Plan packs from a folder
groupings = plan_packs(Path("stickers"), name="My Pack")

# Create in-memory packs
for name, images in groupings.items():
    pack = create_pack(name, images, publisher="Me")
    zip_bytes = pack_to_wastickers(pack)
    Path(f"{pack.id}.wastickers").write_bytes(zip_bytes)
```

### Public API reference

| Function                          | Returns                    | Description                                |
|-----------------------------------|----------------------------|--------------------------------------------|
| `plan_packs(input_dir, name)`     | `dict[str, list[Path]]`    | Scan & group images into packs             |
| `create_pack(name, images, pub)`  | `ProcessedPack`            | Convert images & build pack in memory      |
| `pack_to_wastickers(pack)`        | `bytes`                    | Serialise pack as a `.wastickers` ZIP      |
| `sanitize(name)`                  | `str`                      | Sanitise a string for use as a filename    |
| `scan(folder)`                    | `list[Path]`               | List image files in a folder               |
| `scan_subfolders(path)`           | `list[tuple[str, Path]]`   | List subfolders with their image files     |

| Class              | Fields                                                  |
|--------------------|---------------------------------------------------------|
| `ProcessedPack`    | `id`, `name`, `publisher`, `stickers: list[Image]`, `tray: Image` |

| Exception                  | Description                             |
|----------------------------|-----------------------------------------|
| `StickerError`             | Base for all package errors             |
| `ImageConversionError`     | Image could not be processed            |
| `InputError`               | Input directory or files are invalid    |

## Development

```bash
git clone <repo>
cd whatsappsticker
pip install -e .
pip install pytest
pytest
```

### Running tests

```bash
pytest          # 52 tests covering all modules
pytest -v       # verbose output
pytest -x       # stop on first failure
```

### Project structure

```
whatsappsticker/
├── whatsappsticker/
│   ├── __init__.py      # Empty (CLI-only package)
│   ├── __main__.py      # `python -m whatsappsticker` entry point
│   ├── cli.py           # CLI argument parsing and orchestration
│   ├── wastickers.py    # Image conversion, pack creation, ZIP building
│   ├── scan.py          # File scanning and name sanitisation
│   ├── grouping.py      # Pack planning (subfolder / flat mode)
│   ├── report.py        # HTML preview generation
│   └── exceptions.py    # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Shared fixtures (test images, folders)
│   ├── test_scan.py
│   ├── test_grouping.py
│   ├── test_wastickers.py
│   ├── test_report.py
│   └── test_cli.py
├── pyproject.toml         # Project metadata & build config
├── .gitignore
└── README.md
```

## Limitations

- No webp filename-based matching config (the `example_config.json` is a placeholder for future development)
- Maximum 30 stickers per pack (WhatsApp limitation)
- Each sticker must be ≤100 KB after WebP conversion
- Tray icon is always the first image from the pack

## License

MIT
