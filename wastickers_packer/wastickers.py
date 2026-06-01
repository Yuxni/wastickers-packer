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
MIN_FRAME_DURATION_MS = 10
MAX_FRAME_DURATION_MS = 500
MAX_TOTAL_ANIMATION_MS = 10_000


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
        dur = img.info.get("duration", 100) or 100
        if dur > MAX_FRAME_DURATION_MS:
            logger.warning("Clamping frame %d duration from %dms to %dms", i, dur, MAX_FRAME_DURATION_MS)
            dur = MAX_FRAME_DURATION_MS
        if dur < MIN_FRAME_DURATION_MS:
            logger.warning("Raising frame %d duration from %dms to %dms", i, dur, MIN_FRAME_DURATION_MS)
            dur = MIN_FRAME_DURATION_MS
        durations.append(dur)

    total_dur = sum(durations)
    if total_dur > MAX_TOTAL_ANIMATION_MS:
        scale = MAX_TOTAL_ANIMATION_MS / total_dur
        logger.warning("Total animation %dms exceeds %dms, scaling durations by %.2f",
                       total_dur, MAX_TOTAL_ANIMATION_MS, scale)
        durations = [max(8, int(d * scale)) for d in durations]

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
        logger.info("  sticker_%02d: %s", idx, img_path.name)
        raw = Image.open(img_path)

        if getattr(raw, "is_animated", False):
            n = getattr(raw, "n_frames", 0)
            logger.info("         (%d frames, encoding...)", n)
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
