import logging
from pathlib import Path
from typing import Dict, List, Optional

from .scan import is_animated, scan, scan_subfolders
from .exceptions import InputError

logger = logging.getLogger(__name__)

MAX_PER_PACK = 30
MIN_PER_PACK = 3



def _display_name(raw: str) -> str:
    return raw.replace("_", " ").replace("-", " ").title()


def _split_flat(images: List[Path], base_name: str) -> Dict[str, List[Path]]:
    """Split images into packs of MAX_PER_PACK."""
    count = len(images)
    if count < MIN_PER_PACK:
        raise InputError(f"Need at least {MIN_PER_PACK} stickers, found {count}")
    
    if count < MAX_PER_PACK:
        return {base_name: images}
    
    packs: Dict[str, List[Path]] = {}
    for i in range(0, count, MAX_PER_PACK):
        chunk = images[i:i + MAX_PER_PACK]
        name = f"{base_name} {i // MAX_PER_PACK + 1}"
        packs[name] = chunk
    return packs


def plan_packs(input_dir: Path, name: Optional[str] = None) -> Dict[str, List[Path]]:
    subfolders = scan_subfolders(input_dir)

    if subfolders:
        packs: Dict[str, List[Path]] = {}
        for sub_name, images in subfolders:
            if not (MIN_PER_PACK <= len(images) <= MAX_PER_PACK):
                raise InputError(
                    f"Subfolder '{sub_name}' has {len(images)} sticker(s); "
                    f"must have between {MIN_PER_PACK} and {MAX_PER_PACK}"
                )
            pack_name = _display_name(sub_name)
            animated_count = sum(1 for p in images if is_animated(p))
            if 0 < animated_count < len(images):
                raise InputError(
                    f"Subfolder '{sub_name}' contains both static and "
                    f"animated stickers. Please separate them into "
                    f"different subfolders."
                )
            packs[pack_name] = images
        return packs

    images = scan(input_dir)
    if not images:
        raise InputError(f"No supported image files found in {input_dir}")

    logger.info("Found %d images", len(images))
    pack_name = name if name else _display_name(input_dir.name)

    animated = [p for p in images if is_animated(p)]
    static = [p for p in images if not is_animated(p)]

    packs: Dict[str, List[Path]] = {}
    
    if animated and static:

        packs.update(_split_flat(animated, pack_name + " Animated"))
        packs.update(_split_flat(static, pack_name + " Static"))
    elif animated:
        packs.update(_split_flat(animated, pack_name))
    else:
        packs.update(_split_flat(static, pack_name))
    return packs
