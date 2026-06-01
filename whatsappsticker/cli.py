import logging
import sys
from pathlib import Path

from .grouping import plan_packs
from .wastickers import create_pack, pack_to_wastickers
from .report import write_index
from .exceptions import StickerError


def _setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(
        prog="whatsappsticker",
        description="Pack sticker images into .wastickers files for WhatsApp.",
    )
    ap.add_argument("input", help="Folder with sticker images or subdirectories")
    ap.add_argument("-o", "--output", default="output",
                    help="Output directory (default: output/)")
    ap.add_argument("--publisher", default="WhatsApp Sticker Tool",
                    help="Publisher name in metadata")
    ap.add_argument("--name",
                    help="Pack name (for flat folders without subdirectories)")
    ap.add_argument("--report", action="store_true",
                    help="Generate HTML preview page with tray icons")

    args = ap.parse_args()
    _setup_logging()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.is_dir():
        logging.error("%s is not a directory", input_dir)
        sys.exit(1)

    try:
        groupings = plan_packs(input_dir=input_dir, name=args.name)

        packs = [create_pack(name, images, publisher=args.publisher)
                 for name, images in groupings.items()]

        if not packs:
            logging.error("No valid packs generated.")
            sys.exit(1)

        wastickers_files = [pack_to_wastickers(pack) for pack in packs]

        output_dir.mkdir(parents=True, exist_ok=True)

        for pack, zip_bytes in zip(packs, wastickers_files):
            (output_dir / f"{pack.id}.wastickers").write_bytes(zip_bytes)
            logging.info("wrote %s.wastickers", pack.id)

        if args.report:
            write_index(output_dir, packs)
            logging.info("Wrote preview at: %s/index.html", output_dir.resolve())

        logging.info("Done. Output in: %s", output_dir.resolve())
    except StickerError as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    cli()
