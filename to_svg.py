#!/usr/bin/env python3
"""Convert PNG flat illustrations to color SVG vectors using vtracer."""
import argparse
from pathlib import Path

import vtracer


def main():
    parser = argparse.ArgumentParser(description="Konversi PNG -> SVG (vtracer).")
    parser.add_argument("src", type=Path, help="Folder berisi PNG")
    parser.add_argument("dst", type=Path, help="Folder output SVG")
    parser.add_argument("--mode", default="spline", help="spline atau polygon (default spline)")
    parser.add_argument("--speckle", type=int, default=8, help="filter_speckle (default 8)")
    parser.add_argument("--precision", type=int, default=8, help="color_precision (default 8)")
    args = parser.parse_args()

    if not args.src.is_dir():
        raise SystemExit(f"Folder tidak ada: {args.src}")
    args.dst.mkdir(parents=True, exist_ok=True)

    pngs = sorted(args.src.glob("*.png"))
    if not pngs:
        raise SystemExit(f"Tidak ada PNG di {args.src}")
    for png in pngs:
        out = args.dst / (png.stem + ".svg")
        vtracer.convert_image_to_svg_py(
            str(png),
            str(out),
            colormode="color",
            mode=args.mode,
            filter_speckle=args.speckle,
            color_precision=args.precision,
        )
        print(f"  {png.name} -> {out.name} ({out.stat().st_size // 1024} KB)")
    print(f"Selesai: {len(pngs)} SVG di {args.dst}")


if __name__ == "__main__":
    main()