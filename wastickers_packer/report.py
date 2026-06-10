from io import BytesIO
from pathlib import Path
from typing import List

from .wastickers import ProcessedPack


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def write_index(output_dir: Path, packs: List[ProcessedPack]) -> None:
    """Write the HTML preview page with tray icons and sticker previews."""
    cards = ""
    for p in packs:
        pack_dir = output_dir / p.id
        pack_dir.mkdir(parents=True, exist_ok=True)

        (pack_dir / "tray.png").write_bytes(p.tray)

        thumbs = ""
        for i, sticker in enumerate(p.stickers):
            if isinstance(sticker, bytes):
                (pack_dir / f"sticker_{i + 1:02d}.webp").write_bytes(sticker)
                thumbs += f'<img src="{p.id}/sticker_{i + 1:02d}.webp" alt="">\n'
            else:
                buf = BytesIO()
                sticker.save(buf, "PNG")
                (pack_dir / f"sticker_{i + 1:02d}.png").write_bytes(buf.getvalue())
                thumbs += f'<img src="{p.id}/sticker_{i + 1:02d}.png" alt="">\n'

        cards += f"""<div class="card">
  <div class="card-header">
    <img src="{p.id}/tray.png" alt="">
    <div>
      <h3>{_esc(p.name)}</h3>
      <p>{_esc(p.publisher)} &middot; {len(p.stickers)} stickers</p>
    </div>
  </div>
  <div class="stickers">
{thumbs}  </div>
</div>\n"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Sticker Packs</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{font-family:-apple-system,BlinkMacSystemFont,sans-serif;
       background:#0d1418;color:#e9edef;padding:24px}}
.container {{max-width:520px;margin:0 auto}}
h1 {{font-size:24px;margin-bottom:24px}}
.card {{background:#182229;border-radius:16px;padding:16px;margin-bottom:16px}}
.card-header {{display:flex;align-items:center;gap:16px;margin-bottom:12px}}
.card-header img {{width:64px;height:64px;border-radius:12px}}
.card-header h3 {{font-size:16px}}
.card-header p {{color:#8696a0;font-size:13px;margin-top:2px}}
.stickers {{display:flex;flex-wrap:wrap;gap:8px}}
.stickers img {{width:72px;height:72px;border-radius:8px;background:#0d1418}}
</style>
</head>
<body><div class="container">
<h1>Sticker Packs</h1>
{cards}
<p style="color:#8696a0;font-size:12px;margin-top:24px">Generated with whatsappsticker</p>
</div></body></html>"""

    (output_dir / "index.html").write_text(html, encoding="utf-8")
