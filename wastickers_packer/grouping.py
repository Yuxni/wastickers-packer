import logging
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import InputError
from .scan import scan, scan_subfolders

logger = logging.getLogger(__name__)

MAX_PER_PACK = 30
MIN_PER_PACK = 3


def _display_name(raw: str) -> str:
    return raw.replace("_", " ").replace("-", " ").title()


def _pad(images: List[Path]) -> List[Path]:
    """Pad *images* to MIN_PER_PACK by cycling existing stickers."""
    count = len(images)
    if count >= MIN_PER_PACK or count == 0:
        return images
    padded = list(images)
    while len(padded) < MIN_PER_PACK:
        padded.append(images[len(padded) % count])
    logger.warning("Padded from %d to %d stickers by duplicating", count, len(padded))
    return padded


def _split_flat(images: List[Path], base_name: str) -> Dict[str, List[Path]]:
    """Split images into packs of MAX_PER_PACK."""
    images = _pad(images)
    if not images:
        return {}
    count = len(images)

    if count < MAX_PER_PACK:
        return {base_name: images}

    packs: Dict[str, List[Path]] = {}
    for i in range(0, count, MAX_PER_PACK):
        chunk = images[i : i + MAX_PER_PACK]
        name = f"{base_name} {i // MAX_PER_PACK + 1}"
        packs[name] = chunk
    return packs


def plan_packs(input_dir: Path, name: Optional[str] = None) -> Dict[str, List[Path]]:
    subfolders = scan_subfolders(input_dir)

    if subfolders:
        packs: Dict[str, List[Path]] = {}
        for sub_name, images in subfolders:
            if len(images) > MAX_PER_PACK:
                raise InputError(
                    f"Subfolder '{sub_name}' has {len(images)} sticker(s); "
                    f"maximum per pack is {MAX_PER_PACK}"
                )
            pack_name = _display_name(sub_name)
            packs.update(_split_flat(images, pack_name))
        return packs

    images = scan(input_dir)
    if not images:
        raise InputError(f"No supported image files found in {input_dir}")

    logger.info("Found %d images", len(images))
    pack_name = name if name else _display_name(input_dir.name)
    return _split_flat(images, pack_name)
