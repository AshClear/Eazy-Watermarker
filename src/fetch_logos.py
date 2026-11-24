#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可选脚本：把品牌标志下载到 logos/ 目录。

仓库本身**不附带**任何品牌标志（商标问题），所以给你两条路：
  1) 不下载 —— 直接用文字字标（程序自带，效果不差）
  2) 跑这个脚本，按需下载

用法：
    python src/fetch_logos.py --list                  # 看有哪些、能下哪个源
    python src/fetch_logos.py --all                   # 全部下载（默认源）
    python src/fetch_logos.py --only sony canon       # 只下指定品牌
    python src/fetch_logos.py --all --source jsdelivr # 换源（国内网络用这个）
    python src/fetch_logos.py --all --dry-run         # 只打印 URL，不下载

源：
    commons   Wikimedia Commons 原件（矢量、全球可用；国内网络可能连不上）
    jsdelivr  Simple Icons（国内可直连，但是单色图标，且只有 8 个品牌有）

注意：品牌标志是各公司的商标，下载/使用请自行确认使用范围（个人作品一般没问题）。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "logos"

COMMONS = "https://upload.wikimedia.org/wikipedia/commons"
JSDELIVR = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons"

# brand: (Commons 文件名, 是否完整标) , Simple Icons slug
CATALOG = {
    "nikon":      (("Nikon_Logo.svg", True),           "nikon"),
    "sony":       (("Sony_logo.svg", False),           "sony"),
    "canon":      (("Canon_wordmark.svg", False),      None),
    "fujifilm":   (("Fujifilm_logo.svg", False),       "fujifilm"),
    "panasonic":  (("Lumix_logo.svg", False),          "panasonic"),
    "om":         (("OM-System-Logo.svg", False),      None),
    "leica":      (("Leica_Camera.svg", False),        "leica"),
    "pentax":     (("Pentax_Logo.svg", False),         None),
    "ricoh":      (("Ricoh_logo_2012.svg", False),     None),
    "hasselblad": (("Hasselblad_logo.svg", False),     None),
    "dji":        (("DJI_Innovations_logo.svg", False), "dji"),
    "sigma":      (("SIGMA_CORPORATION.svg", False),   None),
    "apple":      (("Apple_logo_black.svg", False),    "apple"),
    "google":     (("Google_2015_logo.svg", False),    "google"),
}


def commons_url(filename: str) -> str:
    """Wikimedia 的路径就是文件名的 md5：<首字符>/<前两位>/<文件名>。"""
    h = hashlib.md5(filename.encode("utf-8")).hexdigest()
    return f"{COMMONS}/{h[0]}/{h[:2]}/{filename}"


def target_name(brand: str, seal: bool, ext: str = ".svg") -> str:
    return f"{brand}-{'seal' if seal else 'wordmark'}{ext}"


def fetch(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Eazy-Watermarker/1.0 (logo fetch; +https://github.com/)",
        "Accept": "image/svg+xml,image/png,*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def looks_like_svg(data: bytes) -> bool:
    head = data[:400].lstrip().lower()
    return b"<svg" in head or head.startswith(b"<?xml")


def main() -> int:
    ap = argparse.ArgumentParser(description="下载品牌标志到 logos/")
    ap.add_argument("--all", action="store_true", help="下载全部")
    ap.add_argument("--only", nargs="+", metavar="BRAND", help="只下这些品牌")
    ap.add_argument("--source", choices=["commons", "jsdelivr"], default="commons")
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="输出目录（默认 logos/）")
    ap.add_argument("--list", action="store_true", help="列出品牌与可用源")
    ap.add_argument("--dry-run", action="store_true", help="只打印下载地址")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    args = ap.parse_args()

    if args.list:
        print(f"{'brand':<12} {'commons':<34} jsdelivr")
        for brand, ((fname, seal), si) in CATALOG.items():
            print(f"{brand:<12} {target_name(brand, seal):<34} {si or '-'}")
        return 0

    brands = list(CATALOG) if args.all else (args.only or [])
    if not brands:
        ap.print_help()
        return 1

    bad = [b for b in brands if b not in CATALOG]
    if bad:
        print(f"未知品牌：{', '.join(bad)}")
        return 1

    out_dir = Path(args.dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = fail = skip = 0
    for brand in brands:
        (fname, seal), si = CATALOG[brand]

        if args.source == "commons":
            url, name, is_seal = commons_url(fname), target_name(brand, seal), seal
        else:
            if not si:
                print(f"[跳过] {brand:<12} jsdelivr 没有这个图标")
                skip += 1
                continue
            url, name, is_seal = f"{JSDELIVR}/{si}.svg", target_name(brand, False), False

        dst = out_dir / name
        if args.dry_run:
            print(f"[URL ] {brand:<12} {url}  ->  {name}")
            continue

        if dst.exists() and not args.force:
            print(f"[已有] {brand:<12} {name}")
            skip += 1
            continue

        try:
            data = fetch(url)
            if len(data) < 300 or not (looks_like_svg(data) or data[:4] == b"\x89PNG"):
                raise ValueError(f"内容不像图片（{len(data)} 字节）")
            dst.write_bytes(data)
            print(f"[OK  ] {brand:<12} {name}  ({len(data)/1024:.1f} KB)")
            ok += 1
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as e:
            print(f"[失败] {brand:<12} {e}")
            fail += 1

    if not args.dry_run:
        print(f"\n完成：成功 {ok}，跳过 {skip}，失败 {fail}")
        if fail:
            print("提示：国内网络连不上 Wikimedia 时，试试  --source jsdelivr（只有 8 个品牌有）")
            print("      或者手动从官网 / Wikimedia 页面保存 SVG，命名规则见 logos/README.md")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
