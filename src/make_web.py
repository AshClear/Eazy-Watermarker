#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把模板 + 内置标志打包成单文件离线网页。

    python src/make_web.py                        -> build/web/index.html
    python src/make_web.py --demo-image docs/demo.jpg
                                                  -> build/web/demo.html（自测用）
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # 仓库根
SRC = Path(__file__).resolve().parent
TPL = SRC / "web_template.html"
LOGO_DIR = ROOT / "logos"
OUT_DIR = ROOT / "build" / "web"


def svg_data_uri(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    # 没写 width/height 的 SVG，浏览器可能算不出内在尺寸，补上
    if not re.search(r"<svg[^>]*\bwidth=", text, re.I):
        m = re.search(r'viewBox="\s*([\d.+-]+)[ ,]+([\d.+-]+)[ ,]+([\d.+-]+)[ ,]+([\d.+-]+)', text)
        if m:
            w, h = m.group(3), m.group(4)
            text = re.sub(r"<svg", f'<svg width="{w}" height="{h}"', text, count=1)
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return "data:image/svg+xml;base64," + b64


def png_data_uri(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + b64


def collect_logos() -> dict:
    out = {}
    if not LOGO_DIR.is_dir():
        return out
    files = {p.stem.lower(): p for p in LOGO_DIR.iterdir()
             if p.is_file() and p.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg"}}
    brands = set()
    for stem in files:
        base = re.sub(r"-(seal|wordmark|logo)$", "", stem)
        brands.add(base)

    for brand in sorted(brands):
        pick = None
        seal = False
        for cand, is_seal in ((f"{brand}-seal", True), (f"{brand}-wordmark", False),
                              (f"{brand}-logo", False), (brand, True)):
            if cand in files:
                pick, seal = files[cand], is_seal
                break
        if not pick:
            continue
        uri = svg_data_uri(pick) if pick.suffix.lower() == ".svg" else png_data_uri(pick)
        out[brand] = {"uri": uri, "seal": seal}
        print(f"[logo] {brand:<12} {pick.name:<24} seal={seal}  {len(uri)//1024}KB")
    return out


def build(html: str, logos: dict, demo_uri: str | None) -> str:
    html = html.replace("__LOGOS__", json.dumps(logos, ensure_ascii=False))
    if demo_uri:
        html = html.replace(
            "/* ============================== 启动 ============================== */",
            "const DEMO_URI = %s;\n" % json.dumps(demo_uri))
        html = html.replace("fillBrandSelect();", """fillBrandSelect();
(async () => {
  const blob = await (await fetch(DEMO_URI)).blob();
  const f = new File([blob], "DEMO_4707.jpg", {type:"image/jpeg"});
  addFiles([f]);
})();""")
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-image", default=None,
                    help="生成一个把该图片内嵌进去的 demo.html（自测/截图用）")
    ap.add_argument("--demo", action="store_true", help="兼容旧参数，等同 --demo-image docs/demo.jpg")
    args = ap.parse_args()

    logos = collect_logos()
    html = TPL.read_text(encoding="utf-8")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = OUT_DIR / "index.html"
    dst.write_text(build(html, logos, None), encoding="utf-8")
    print(f"[OK] {dst}  ({dst.stat().st_size/1024:.0f} KB, {len(logos)} logos)")

    demo_src = args.demo_image or (str(ROOT / "docs" / "demo.jpg") if args.demo else None)
    if demo_src:
        from PIL import Image

        src = Path(demo_src)
        with Image.open(src) as im:
            exif = im.getexif()
            im = im.copy()
            im.thumbnail((1000, 1000), Image.LANCZOS)
            buf = OUT_DIR / "_demo.jpg"
            im.save(buf, "JPEG", quality=88, exif=exif.tobytes())
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.read_bytes()).decode("ascii")
        demo_dst = OUT_DIR / "demo.html"
        demo_dst.write_text(build(html, logos, uri), encoding="utf-8")
        buf.unlink(missing_ok=True)
        print(f"[demo] {demo_dst}  ({demo_dst.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
