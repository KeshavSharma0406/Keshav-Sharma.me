"""Turn the prepared photo into ascii-portrait.svg.

The panel is light text on a dark background, so bright parts of the face get
dense characters and the removed background stays blank. (A dark-is-dense ramp
would come out as a photo negative here.)

    python scripts/make_ascii_svg.py --crop 390 85 1068 790

--crop frames the face in the prepared image, so it's specific to each photo.
Those values match the current photo. Leave it out to frame the whole subject.
"""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter

from svg_common import BAR_HEIGHT, BG, ROOT, TEXT, window

DEFAULT_IN = ROOT / "photo" / "prepped.png"
DEFAULT_OUT = ROOT / "ascii-portrait.svg"

# Same height as info-card.svg so the two line up side by side in the README.
WIDTH, HEIGHT = 430, 480
COLS, ROWS = 120, 62
CELL_W, CELL_H = 400 / COLS, 416 / ROWS
FONT_SIZE = 5.5
RAMP = " .`:-=+*cs#%@"  # dark (sparse) -> bright (dense)
STAGGER_MS = 28


def load_brightness(path, crop=None):
    """Return a ROWS x COLS array of 0..1 brightness, with the background at 0."""
    image = Image.open(path).convert("RGBA")
    bbox = crop or image.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    if bbox:
        image = image.crop(bbox)

    # Cover the character grid, anchored to the top so the head is never cut off.
    target = (COLS * CELL_W) / (ROWS * CELL_H)
    w, h = image.size
    if w / h > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        image = image.crop((left, 0, left + new_w, h))
    else:
        image = image.crop((0, 0, w, int(w / target)))

    image = image.resize((COLS, ROWS), Image.LANCZOS)
    alpha = np.asarray(image.getchannel("A"), dtype=float) / 255
    grey = image.convert("RGB").convert("L").filter(ImageFilter.UnsharpMask(radius=1.2, percent=130))
    grey = np.asarray(grey, dtype=float)

    subject = grey[alpha > 0.5]
    if subject.size:
        low, high = np.percentile(subject, [3, 98])
        grey = (grey - low) / max(high - low, 1)
    return np.clip(grey, 0, 1) * alpha


def to_rows(brightness, gamma, floor):
    """gamma below 1 lifts midtones; values under floor go blank to clear speckle."""
    toned = np.where(brightness < floor, 0, brightness) ** gamma
    indexes = (toned * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row) for row in indexes]


def render(rows):
    css = (
        "@keyframes wipe{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        ".w{transform-box:fill-box;transform-origin:right center;"
        "animation:wipe .45s steps(24) both}"
        "@media (prefers-reduced-motion:reduce){.w{display:none}}"
    )
    x = (WIDTH - COLS * CELL_W) / 2
    top = BAR_HEIGHT + (HEIGHT - BAR_HEIGHT - ROWS * CELL_H) / 2
    text_width = COLS * CELL_W

    parts = []
    for i, row in enumerate(rows):
        y = top + i * CELL_H
        # textLength keeps columns aligned whichever monospace font the viewer has.
        parts.append(
            f'<text x="{x}" y="{y + CELL_H - 1.3:.2f}" xml:space="preserve" font-size="{FONT_SIZE}" '
            f'textLength="{text_width}" lengthAdjust="spacing" fill="{TEXT}">{escape(row)}</text>'
        )
    # Background-coloured covers that shrink away reveal each row. With reduced
    # motion they are hidden, leaving the finished portrait.
    for i in range(len(rows)):
        y = top + i * CELL_H
        parts.append(
            f'<rect class="w" style="animation-delay:{i * STAGGER_MS}ms" x="{x - 1}" y="{y:.2f}" '
            f'width="{text_width + 2}" height="{CELL_H + 0.5:.2f}" fill="{BG}"/>'
        )
    return window(WIDTH, HEIGHT, "portrait.txt", css, "\n".join(parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--crop", type=int, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                        help="pixel box in the prepared image; default is the whole subject")
    parser.add_argument("--gamma", type=float, default=0.6)
    parser.add_argument("--floor", type=float, default=0.06)
    args = parser.parse_args()
    brightness = load_brightness(args.input, tuple(args.crop) if args.crop else None)
    args.out.write_text(render(to_rows(brightness, args.gamma, args.floor)), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
