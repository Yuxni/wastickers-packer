import re
from pathlib import Path
from typing import List, Tuple

from PIL import Image

IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}


def is_animated(path: Path) -> bool:
    """Check whether *path* points to a multi-frame image (animated WebP / GIF)."""
    with Image.open(path) as img:
        return getattr(img, "is_animated", False)


def sanitize(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "pack"


def scan(folder: Path) -> List[Path]:
    files = []
    for f in folder.iterdir():
        if not f.is_file():
            continue
        if f.name.startswith("."):
            continue
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        files.append(f)
    files.sort()
    return files


def scan_subfolders(path: Path) -> List[Tuple[str, List[Path]]]:
    entries = []
    for entry in sorted(path.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        images = scan(entry)
        if images:
            entries.append((entry.name, images))
    return entries
