#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行批量加水印（无界面）。

    python src/cli.py 照片文件夹
    python src/cli.py a.jpg b.png -o out --quality 90
    python src/cli.py photos --brand sony --model "α7 IV" --seal 130
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

import core

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
ROOT = Path(__file__).resolve().parent.parent


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += [f for f in sorted(p.iterdir()) if f.is_file() and f.suffix.lower() in IMG_EXT]
        elif p.is_file():
            files.append(p)
        else:
            print(f"[跳过] 找不到：{p}")
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="白边 + 机型/镜头/参数 + 品牌标识")
    ap.add_argument("paths", nargs="+", help="图片或文件夹")
    ap.add_argument("-o", "--out", default=None, help="输出目录（默认 源目录/framed）")
    ap.add_argument("--border", type=float, default=3.5, help="白边，占短边百分比（默认 3.5）")
    ap.add_argument("--scale", type=float, default=100, help="字号百分比（默认 100）")
    ap.add_argument("--seal", type=float, default=150, help="标识大小百分比（默认 150）")
    ap.add_argument("--quality", type=int, default=92, help="JPEG 质量（默认 92）")
    ap.add_argument("--template", default="{focal} · {aperture} · {shutter} · {iso}")
    ap.add_argument("--no-date", action="store_true")
    ap.add_argument("--no-lens", action="store_true")
    ap.add_argument("--no-meta", action="store_true")
    ap.add_argument("--no-brand", action="store_true")
    ap.add_argument("--brand", default=None, help="强制品牌代号：nikon/sony/canon/...")
    ap.add_argument("--model", default=None, help="强制机型文字")
    ap.add_argument("--logo-dir", default=str(ROOT / "logos"), help="品牌标志目录")
    args = ap.parse_args()

    files = collect(args.paths)
    if not files:
        print("没有找到图片。")
        return 1

    opts = core.Options()
    opts.border = max(0.003, args.border / 100)
    opts.scale = args.scale / 100
    opts.seal_scale = args.seal / 100
    opts.logo_scale = opts.seal_scale * 0.35
    opts.template = args.template
    opts.show_date = not args.no_date
    opts.show_lens = not args.no_lens
    opts.show_meta = not args.no_meta
    opts.show_brand = not args.no_brand
    opts.model_override = args.model or ""

    logo_dir = Path(args.logo_dir)
    ok = 0
    for src in files:
        try:
            with Image.open(src) as im0:
                meta = core.read_meta(im0)
            if args.brand and args.brand.lower() in core.BRANDS:
                meta["brand"] = args.brand.lower()

            path, seal = core.find_logo(logo_dir, meta["brand"])
            logo = None
            if path:
                try:
                    logo = core.load_logo(path, 600, seal=seal)
                except Exception as e:
                    print(f"  [提示] 标志渲染失败 {path.name}: {e}")

            im = core.load_image(src)
            out = core.render(im, meta, opts, logo, seal)

            out_dir = Path(args.out) if args.out else src.parent / "framed"
            out_dir.mkdir(parents=True, exist_ok=True)
            dst = out_dir / f"{src.stem}_wm.jpg"
            core.save_jpeg(out, dst, args.quality)
            print(f"[OK] {src.name} -> {dst}")
            ok += 1
        except Exception as e:
            print(f"[失败] {src.name}: {e}")

    print(f"\n完成 {ok}/{len(files)} 张。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
