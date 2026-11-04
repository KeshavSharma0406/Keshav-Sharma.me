"""Cut the subject out of a photo and boost local contrast. Run once per photo,
locally. The photo and its output are git-ignored and never needed in CI.

    python scripts/prep_photo.py path/to/photo.jpg
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from rembg import remove

from svg_common import ROOT

DEFAULT_OUT = ROOT / "photo" / "prepped.png"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clahe", type=float, default=3.0,
                        help="local contrast boost; higher values reveal more in deep shadow")
    args = parser.parse_args()

    # exif_transpose: phone photos are often stored rotated.
    image = ImageOps.exif_transpose(Image.open(args.photo)).convert("RGB")
    image.thumbnail((1400, 1400))

    cutout = np.array(remove(image).convert("RGBA"))
    rgb, alpha = cutout[..., :3], cutout[..., 3]

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=args.clahe, tileGridSize=(8, 8)).apply(lab[..., 0])
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.dstack([rgb, alpha]), "RGBA").save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
