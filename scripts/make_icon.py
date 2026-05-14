"""Generate a 1024x1024 Slack app icon for the HWP→PDF preview bot."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
OUT = Path(__file__).resolve().parent.parent / "assets" / "icon.png"

BG = (245, 247, 250, 255)         # soft off-white square
BG_RADIUS = 180

HWP_FILL = (30, 110, 200, 255)    # 한컴-ish blue
HWP_DARK = (20, 80, 160, 255)
PDF_FILL = (220, 50, 50, 255)     # PDF red
PDF_DARK = (170, 25, 25, 255)
PAGE_W = 340
PAGE_H = 440
FOLD = 70                          # corner fold size
ARROW = (60, 60, 70, 255)


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _doc(draw: ImageDraw.ImageDraw, x: int, y: int, fill, dark, label: str) -> None:
    """Draw a rounded-rectangle page with a folded top-right corner and label."""
    radius = 32

    # main body
    draw.rounded_rectangle(
        (x, y, x + PAGE_W, y + PAGE_H),
        radius=radius,
        fill=fill,
    )

    # fold triangle (darker shade)
    fold_pts = [
        (x + PAGE_W - FOLD, y),
        (x + PAGE_W, y + FOLD),
        (x + PAGE_W - FOLD, y + FOLD),
    ]
    # clear the corner that the fold occupies (subtract the bg)
    draw.polygon(
        [(x + PAGE_W - FOLD, y), (x + PAGE_W, y), (x + PAGE_W, y + FOLD)],
        fill=BG,
    )
    draw.polygon(fold_pts, fill=dark)

    # label
    font = _font(110)
    bbox = draw.textbbox((0, 0), label, font=font, anchor="lt")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (PAGE_W - tw) // 2 - bbox[0]
    ty = y + (PAGE_H - th) // 2 - bbox[1] + 30  # nudge below the fold
    draw.text((tx, ty), label, font=font, fill=(255, 255, 255, 255))


def _arrow(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    """Draw a chunky right-arrow at (cx, cy) centered."""
    shaft_len = 90
    shaft_h = 30
    head_w = 70
    head_h = 90

    # shaft
    draw.rectangle(
        (cx - shaft_len // 2, cy - shaft_h // 2,
         cx + shaft_len // 2, cy + shaft_h // 2),
        fill=ARROW,
    )
    # head
    head_left = cx + shaft_len // 2 - 10
    draw.polygon(
        [
            (head_left, cy - head_h // 2),
            (head_left + head_w, cy),
            (head_left, cy + head_h // 2),
        ],
        fill=ARROW,
    )


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # rounded square background
    draw.rounded_rectangle(
        (0, 0, SIZE, SIZE),
        radius=BG_RADIUS,
        fill=BG,
    )

    # two pages with arrow between them, centered
    gap = 130
    total_w = PAGE_W * 2 + gap
    left_x = (SIZE - total_w) // 2
    right_x = left_x + PAGE_W + gap
    page_y = (SIZE - PAGE_H) // 2

    _doc(draw, left_x, page_y, HWP_FILL, HWP_DARK, "HWP")
    _doc(draw, right_x, page_y, PDF_FILL, PDF_DARK, "PDF")
    _arrow(draw, SIZE // 2, page_y + PAGE_H // 2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
