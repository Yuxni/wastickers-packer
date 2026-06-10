"""End-to-end benchmark — generates fake images and times the full pipeline.

Usage:
    python tests/bench_e2e.py
    python tests/bench_e2e.py --frames 200   # GIF with 200 frames
"""

import argparse
import logging
import sys
import tempfile
import time
from pathlib import Path

# Ensure the project root is on sys.path when run directly
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PIL import Image  # noqa: E402

from wastickers_packer.grouping import plan_packs  # noqa: E402
from wastickers_packer.wastickers import create_pack, pack_to_wastickers  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("bench")


def make_static(width=512, height=512, color=(255, 0, 0)):
    return Image.new("RGBA", (width, height), color + (255,))


def make_animated(n_frames, width=512, height=512):
    frames = []
    for i in range(n_frames):
        r = (i * 10) % 256
        g = (i * 20) % 256
        b = (i * 30) % 256
        frame = Image.new("RGBA", (width, height), (r, g, b, 255))
        frames.append(frame)
    buf = tempfile.SpooledTemporaryFile()
    frames[0].save(
        buf,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    buf.seek(0)
    return buf.read()


def populate_dir(tmpdir: Path, count: int, animated: int = 0, n_frames: int = 50):
    """Write *count* sticker images into *tmpdir*.

    First *animated* images are multi-frame GIFs; the rest are static PNGs.
    """
    for i in range(1, count + 1):
        if i <= animated:
            data = make_animated(n_frames)
            (tmpdir / f"anim_{i:03d}.gif").write_bytes(data)
        else:
            make_static().save(tmpdir / f"static_{i:03d}.png")


def bench(name, images_dir, *, label=None):
    label = label or name
    t0 = time.perf_counter()
    packs = plan_packs(images_dir, name=name)
    t1 = time.perf_counter()
    logger.info("  plan:    %6.2fs", t1 - t0)

    for pack_name, pack_images in packs.items():
        t2 = time.perf_counter()
        processed = create_pack(pack_name, pack_images, publisher="bench")
        t3 = time.perf_counter()
        wastickers = pack_to_wastickers(processed)
        logger.info(
            "  convert: %6.2fs  (%s, %d stickers, %.1f KB)",
            t3 - t2,
            pack_name,
            len(pack_images),
            len(wastickers) / 1024,
        )


def main():
    parser = argparse.ArgumentParser(description="E2E benchmark for wastickers-packer")
    parser.add_argument("--frames", type=int, default=50, help="Frames per animated GIF")
    args = parser.parse_args()

    logger.info("Benchmark: wastickers-packer E2E")
    logger.info("=" * 42)
    logger.info("")

    with tempfile.TemporaryDirectory() as root:
        root = Path(root)

        # --- Static only ---
        logger.info("[static] 3 stickers")
        d = root / "static_3"
        d.mkdir()
        populate_dir(d, 3)
        bench("static_3", d)

        logger.info("")
        logger.info("[static] 15 stickers")
        d = root / "static_15"
        d.mkdir()
        populate_dir(d, 15)
        bench("static_15", d)

        logger.info("")
        logger.info("[static] 35 stickers (triggers split into 2 packs)")
        d = root / "static_35"
        d.mkdir()
        populate_dir(d, 35)
        bench("static_35", d)

        logger.info("")
        # --- Animated ---
        logger.info("[animated] 1 GIF, 2 static (%d frames)", args.frames)
        d = root / "mixed"
        d.mkdir()
        populate_dir(d, 3, animated=1, n_frames=args.frames)
        bench("mixed", d)

        logger.info("")
        logger.info("[animated] all GIFs, 3 stickers (%d frames)", args.frames)
        d = root / "anim_all"
        d.mkdir()
        populate_dir(d, 3, animated=3, n_frames=args.frames)
        bench("anim_all", d)

        logger.info("")
        logger.info("[animated] all GIFs, 10 stickers (%d frames)", args.frames)
        d = root / "anim_10"
        d.mkdir()
        populate_dir(d, 10, animated=10, n_frames=args.frames)
        bench("anim_10", d)

    logger.info("")
    logger.info("Done.")


if __name__ == "__main__":
    main()
