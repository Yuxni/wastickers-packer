import logging
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from PIL import Image

from .exceptions import ImageConversionError, StickerError
from .scan import sanitize

logger = logging.getLogger(__name__)

STICKER_SIZE = (512, 512)
TRAY_SIZE = (96, 96)
MAX_STICKER_KB = 100
MAX_ANIMATED_STICKER_KB = 500


@dataclass
class ProcessedPack:
    """Pack after image conversion, kept in memory."""
    id: str
    name: str
    publisher: str
    stickers: List[bytes]
    tray: bytes

def _animated_to_webp(img: Image.Image) -> bytes:
    n_frames = getattr(img, "n_frames", 1)
    frames = []
    durations = []

    for i in range(n_frames):
        img.seek(i)
        frame = img.copy().convert("RGBA")
        frame.thumbnail(STICKER_SIZE, Image.LANCZOS)
        canvas = Image.new("RGBA", STICKER_SIZE, (0, 0, 0, 0))
        x = (STICKER_SIZE[0] - frame.size[0]) // 2
        y = (STICKER_SIZE[1] - frame.size[1]) // 2
        canvas.paste(frame, (x, y), frame)
        frames.append(canvas)
        durations.append(img.info.get("duration", 100))

    quality = 85
    while quality >= 10:
        buf = BytesIO()
        try:
            frames[0].save(
                buf, "WEBP", save_all=True, append_images=frames[1:],
                quality=quality, duration=durations, loop=0,
            )
        except Exception as e:
            raise ImageConversionError(f"Failed to encode animated WebP: {e}")
        if buf.tell() / 1024 <= MAX_ANIMATED_STICKER_KB:
            return buf.getvalue()
        quality -= 5

    buf = BytesIO()
    frames[0].save(
        buf, "WEBP", save_all=True, append_images=frames[1:],
        quality=10, duration=durations, loop=0,
    )
    return buf.getvalue()


def _sticker_to_webp(img: Image.Image) -> bytes:
    img.thumbnail(STICKER_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", STICKER_SIZE, (0, 0, 0, 0))
    x = (STICKER_SIZE[0] - img.size[0]) // 2
    y = (STICKER_SIZE[1] - img.size[1]) // 2
    canvas.paste(img, (x, y), img)

    quality = 85
    while quality >= 10:
        buf = BytesIO()
        try:
            canvas.save(buf, "WEBP", quality=quality)
        except Exception as e:
            raise ImageConversionError(f"Failed to encode as WebP: {e}")
        if buf.tell() / 1024 <= MAX_STICKER_KB:
            return buf.getvalue()
        quality -= 5

    buf = BytesIO()
    canvas.save(buf, "WEBP", quality=10)
    return buf.getvalue()


def _image_to_png(img: Image.Image) -> bytes:
    img.thumbnail(TRAY_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", TRAY_SIZE, (0, 0, 0, 0))
    x = (TRAY_SIZE[0] - img.size[0]) // 2
    y = (TRAY_SIZE[1] - img.size[1]) // 2
    canvas.paste(img, (x, y), img)

    buf = BytesIO()
    try:
        canvas.save(buf, "PNG")
    except Exception as e:
        raise ImageConversionError(f"Failed to encode tray as PNG: {e}")
    buf.seek(0)
    return buf.getvalue()

def _image_to_bytes(img: Image.Image, fmt: str) -> bytes:
    buf = BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def create_pack(name: str, images: List[Path],
                publisher: str) -> ProcessedPack:
    pack_id = sanitize(name)
    logger.info("[%s] %s", pack_id, name)

    sticker_imgs: List[bytes] = []
    first_raw: Optional[Image.Image] = None

    for idx, img_path in enumerate(images, 1):
        raw = Image.open(img_path)

        if getattr(raw, "is_animated", False):
            anim_bytes = _animated_to_webp(raw)
            sticker_imgs.append(anim_bytes)
            if first_raw is None:
                raw.seek(0)
                first_raw = raw.copy().convert("RGBA")
        else:
            raw_rgba = raw.convert("RGBA")
            sticker_imgs.append(_sticker_to_webp(raw_rgba))
            if first_raw is None:
                first_raw = raw_rgba
        logger.info("  sticker_%02d.webp", idx)

    if not sticker_imgs or first_raw is None:
        raise ImageConversionError(f"No valid stickers converted for '{name}'")

    try:
        tray_png = _image_to_png(first_raw)
    except Exception as e:
        raise ImageConversionError(f"Failed to encode tray: {e}")

    logger.info("  tray.png")
    return ProcessedPack(id=pack_id, name=name, publisher=publisher,
                         stickers=sticker_imgs, tray=tray_png)



def pack_to_wastickers(pack: ProcessedPack) -> bytes:
    buf = BytesIO()
    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("author.txt", pack.publisher)
            zf.writestr("title.txt", pack.name)
            zf.writestr("tray.png", pack.tray)
            for i, item in enumerate(pack.stickers):
                if isinstance(item, bytes):
                    zf.writestr(f"sticker_{i+1:02d}.webp", item)
    except OSError as e:
        raise StickerError(f"Failed to build ZIP for '{pack.name}': {e}")

    logger.info("  %s.wastickers", pack.id)
    return buf.getvalue()
