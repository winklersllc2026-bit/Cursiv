"""
Generate cursiv.ico and tray.ico for the Cursiv launcher.
Run: python launcher/resources/gen_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "icons"
OUT.mkdir(exist_ok=True)

BG    = (8,   9,  12, 255)   # matches the website's --bg: #08090C
GOLD  = (255, 215,  0, 255)

SIZES = [16, 32, 48, 64, 128, 256]

# Bold serif "C" (for Cursiv) -- Georgia Bold is the closest system font to
# the site's EB Garamond branding, and stays legible down to 16px, which a
# thinner or more decorative face would not.
_C_GLYPH = "C"
_C_FONT_CANDIDATES = [
    "C:/Windows/Fonts/georgiab.ttf",   # Georgia Bold
    "georgiab.ttf",
]


def _c_font(size: int) -> ImageFont.FreeTypeFont | None:
    for path in _C_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return None


def _draw_c(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: int, scale: float):
    """Gold serif 'C', centered -- falls back to a drawn arc if no font is found."""
    font = _c_font(int(size * scale))
    if font is not None:
        bbox = draw.textbbox((0, 0), _C_GLYPH, font=font)
        gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (cx - gw / 2 - bbox[0], cy - gh / 2 - bbox[1]),
            _C_GLYPH, font=font, fill=GOLD,
        )
        return

    # Font unavailable on this machine -- draw a plain arc so the icon is
    # never blank.
    r = size * scale * 0.36
    w = max(2, int(size * scale * 0.12))
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=55, end=305, fill=GOLD, width=w)


def _draw_cursiv(size: int) -> Image.Image:
    """Black circle, gold serif 'C' -- the app icon."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    # Background circle
    pad = max(1, int(size * 0.04))
    draw.ellipse([pad, pad, size - pad, size - pad], fill=BG)

    _draw_c(draw, cx, cy, size, 0.62)
    return img


def _draw_tray(size: int) -> Image.Image:
    """Transparent bg, gold 'C' only (looks good on dark/light taskbar)."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2
    _draw_c(draw, cx, cy, size, 0.85)
    return img


def _save_ico(draw_fn, path: Path):
    """
    Pillow ICO writer: pass the largest frame; specify sizes= list
    and it auto-downscales each size from that master image.
    """
    master = draw_fn(256)
    master.save(
        path,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
    )
    # Verify
    check = Image.open(path)
    frame_sizes = []
    try:
        i = 0
        while True:
            check.seek(i)
            frame_sizes.append(check.size)
            i += 1
    except EOFError:
        pass
    print(f"  {path.name}: {len(frame_sizes)} frames {frame_sizes} — {path.stat().st_size:,} bytes")


def main():
    print("Generating Cursiv icons...")
    _save_ico(_draw_cursiv, OUT / "cursiv.ico")
    _save_ico(_draw_tray,   OUT / "tray.ico")
    # 256 PNG for Inno Setup wizard image
    _draw_cursiv(256).save(OUT / "cursiv_256.png")
    print("Done.")


if __name__ == "__main__":
    main()
