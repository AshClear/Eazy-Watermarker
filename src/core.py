#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
core.py —— 品牌水印工具的核心逻辑（EXIF 读取 / 机型归一化 / 白边与徽章排版）

不联网，纯本地。被 GUI 和命令行共用。
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

EXIF_IFD = 0x8769
ROMAN = {2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}

# ------------------------------------------------------------------ 品牌表

BRANDS = {
    "nikon":      dict(name="Nikon",      mark="Nikon",      track=0.02, style="sans"),
    "sony":       dict(name="Sony",       mark="SONY",       track=0.17, style="sans"),
    "canon":      dict(name="Canon",      mark="Canon",      track=0.02, style="serif"),
    "fujifilm":   dict(name="Fujifilm",   mark="FUJIFILM",   track=0.04, style="sans"),
    "panasonic":  dict(name="Lumix",      mark="LUMIX",      track=0.12, style="sans"),
    "om":         dict(name="OM System",  mark="OM SYSTEM",  track=0.10, style="sans"),
    "leica":      dict(name="Leica",      mark="LEICA",      track=0.10, style="serif"),
    "pentax":     dict(name="Pentax",     mark="PENTAX",     track=0.06, style="sans"),
    "ricoh":      dict(name="Ricoh",      mark="RICOH",      track=0.08, style="sans"),
    "hasselblad": dict(name="Hasselblad", mark="HASSELBLAD", track=0.06, style="sans"),
    "dji":        dict(name="DJI",        mark="DJI",        track=0.06, style="sans"),
    "sigma":      dict(name="Sigma",      mark="SIGMA",      track=0.06, style="sans"),
    "apple":      dict(name="iPhone",     mark="iPhone",     track=0.02, style="sans"),
    "google":     dict(name="Google",     mark="PIXEL",      track=0.10, style="sans"),
    "unknown":    dict(name="",           mark="",           track=0.0,  style="sans"),
}

BRAND_KEYS = [
    ("nikon", ("NIKON",)),
    ("sony", ("SONY", "ILCE", "ILME", "ILCA")),
    ("canon", ("CANON",)),
    ("fujifilm", ("FUJI",)),
    ("panasonic", ("PANASONIC", "LUMIX", "DC-")),
    ("om", ("OLYMPUS", "OM DIGITAL", "OM SYSTEM")),
    ("leica", ("LEICA",)),
    ("pentax", ("PENTAX",)),
    ("ricoh", ("RICOH", "GR III", "GR IV")),
    ("hasselblad", ("HASSELBLAD",)),
    ("dji", ("DJI",)),
    ("sigma", ("SIGMA",)),
    ("apple", ("APPLE", "IPHONE")),
    ("google", ("GOOGLE", "PIXEL")),
]

# ------------------------------------------------------------------ 常见机型（下拉用）

COMMON_MODELS = {
    "nikon": ["Z6III", "Z6II", "Z6", "Z7II", "Z7", "Z8", "Z9", "Z5II", "Z5",
              "Z50II", "Z50", "Zf", "Zfc", "D850", "D780", "D750", "D500"],
    "sony": ["α7C II", "α7C", "α7 IV", "α7R V", "α7S III", "α1", "α9 III",
             "α6700", "α6600", "ZV-E1", "FX3", "FX30"],
    "canon": ["EOS R5", "EOS R5 Mark II", "EOS R6", "EOS R6 Mark II", "EOS R8",
              "EOS R50", "EOS R6 Mark III", "EOS 5D Mark IV", "EOS R3", "EOS R1"],
    "fujifilm": ["X-T5", "X-T4", "X-H2", "X-H2S", "X100VI", "X100V", "X-S20",
                 "X-Pro3", "GFX100 II", "GFX50S II"],
    "panasonic": ["S5 II", "S5", "S1R", "GH6", "GH7", "G9 II"],
    "om": ["OM-1", "OM-1 Mark II", "OM-5", "E-M1 Mark III"],
    "leica": ["Q3", "M11", "SL3", "Q2"],
    "pentax": ["K-3 Mark III", "K-1 Mark II", "K70"],
    "ricoh": ["GR III", "GR IIIx", "GR IV"],
    "hasselblad": ["X2D 100C", "907X"],
    "dji": ["Mavic 3", "Air 3"],
    "sigma": ["fp L", "fp"],
    "apple": ["iPhone 16 Pro", "iPhone 15 Pro", "iPhone 15"],
    "google": ["Pixel 9 Pro", "Pixel 8 Pro"],
}


def detect_brand(make: str, model: str) -> str:
    s = f"{make or ''} {model or ''}".upper()
    for key, keys in BRAND_KEYS:
        if any(k in s for k in keys):
            return key
    return "unknown"


# ------------------------------------------------------------------ 机型归一化

def _roman(n: int) -> str:
    return ROMAN.get(n, str(n))


def norm_model(brand: str, model: str) -> str:
    m = re.sub(r"\s+", " ", (model or "").strip())
    if not m:
        return ""

    if brand == "nikon":
        m = re.sub(r"(?i)^nikon( corporation)?\s*", "", m)
        m = re.sub(r"(?i)^(Z\s*\d+)_(\d)$",
                   lambda mo: re.sub(r"\s+", "", mo.group(1)) + _roman(int(mo.group(2))), m)
        return m.strip()

    if brand == "sony":
        s = re.sub(r"(?i)^(ILCE|ILME|ILCA)-", "", m).strip()
        mo = re.fullmatch(r"(\d+)([A-Z]*)(?:M(\d))?", s)
        if mo:
            body, suffix, gen = mo.group(1), mo.group(2), mo.group(3)
            out = f"α{body}{suffix}"
            if gen:
                out += " " + _roman(int(gen))
            return out
        return s

    if brand == "canon":
        m = re.sub(r"(?i)^canon\s*", "", m).strip()
        m = re.sub(r"(?i)\bmark\s*(II|III|IV|V)\b",
                   lambda mo: "Mark " + mo.group(1).upper(), m)
        m = re.sub(r"(?i)m(\d)$", lambda mo: " Mark " + _roman(int(mo.group(1))), m)
        return re.sub(r"\s+", " ", m).strip()

    if brand == "fujifilm":
        return re.sub(r"(?i)^fujifilm\s*", "", m).strip()

    if brand == "panasonic":
        m = re.sub(r"(?i)^DC-", "", m).strip()
        m = re.sub(r"(?i)M(\d)$", lambda mo: " " + _roman(int(mo.group(1))), m)
        return m.strip()

    if brand == "om":
        m = re.sub(r"(?i)^(OLYMPUS|OM DIGITAL SOLUTIONS|OM SYSTEM)\s*", "", m).strip()
        m = re.sub(r"(?i)^OM-?\s*", "OM-", m)
        return re.sub(r"(?i)mark\s*(II|III|IV)", lambda mo: "Mark " + mo.group(1).upper(), m).strip()

    if brand in ("leica", "pentax", "ricoh", "hasselblad", "dji", "sigma", "apple", "google"):
        return re.sub(r"(?i)^(LEICA CAMERA AG|LEICA|PENTAX|RICOH IMAGING|HASSELBLAD|DJI|SIGMA|APPLE|GOOGLE)\s*",
                      "", m).strip()

    return m


# ------------------------------------------------------------------ EXIF

def _ratio(v) -> str:
    try:
        f = float(v)
    except Exception:
        return ""
    if f <= 0:
        return ""
    if f >= 1:
        return f"{f:g}s"
    return f"1/{round(1 / f):d}s"


def read_meta(im: Image.Image) -> dict:
    meta = dict(make="", model="", lens="", focal="", aperture="", shutter="", iso="",
                date="", brand="unknown", title="", lensline="", metaline="", raw_model="")
    try:
        ex = im.getexif()
    except Exception:
        return meta
    if not ex:
        return meta

    meta["make"] = str(ex.get(0x010F, "") or "")
    meta["raw_model"] = str(ex.get(0x0110, "") or "")
    try:
        sub = ex.get_ifd(EXIF_IFD)
    except Exception:
        sub = {}

    def g(tag):
        v = sub.get(tag)
        if v in (None, ""):
            v = ex.get(tag)
        return v

    meta["lens"] = str(g(0xA434) or "").strip()

    fl = g(0x920A)
    if fl:
        try:
            f = float(fl)
            meta["focal"] = f"{round(f)}mm"
            fl35 = g(0xA405)
            if fl35 and abs(float(fl35) - f) > 0.6:
                meta["focal"] += f" ({round(float(fl35))}mm)"
        except Exception:
            pass

    fn = g(0x829D)
    if fn:
        try:
            meta["aperture"] = f"f/{float(fn):g}"
        except Exception:
            pass

    et = g(0x829A)
    if et:
        meta["shutter"] = _ratio(et)

    iso = g(0x8827)
    if iso:
        try:
            iso = iso[0] if isinstance(iso, (list, tuple)) else iso
            meta["iso"] = f"ISO{int(iso)}"
        except Exception:
            pass

    dto = str(g(0x9003) or g(0x0132) or "")
    if re.match(r"^\d{4}:\d{2}:\d{2}", dto):
        meta["date"] = dto.replace(":", "-", 2)[:16]
        meta["date"] = re.sub(r"^(\d{4})-(\d{2})-(\d{2})[ T]", r"\1-\2-\3 ", meta["date"])

    meta["brand"] = detect_brand(meta["make"], meta["raw_model"])
    return meta


# ------------------------------------------------------------------ 字体

SANS_BOLD = ["arialbd.ttf", "seguisb.ttf", "segoeuib.ttf", "bahnschrift.ttf",
             "msyhbd.ttc", "DejaVuSans-Bold.ttf"]
SANS_REG = ["arial.ttf", "segoeui.ttf", "bahnschrift.ttf", "msyh.ttc", "DejaVuSans.ttf"]
SERIF_BOLD = ["timesbd.ttf", "georgiab.ttf", "constanb.ttf", "DejaVuSerif-Bold.ttf",
              "arialbd.ttf"]


def _font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def font_for(kind: str, size: int, style: str = "sans"):
    if style == "serif":
        return _font(SERIF_BOLD, size)
    return _font(SANS_BOLD if kind == "bold" else SANS_REG, size)


# ------------------------------------------------------------------ logo 载入

def _patch_svglib_clip():
    import svglib.svglib as svgmod
    if getattr(svgmod, "_clip_patched", False):
        return
    orig = svgmod._shape_to_pdf_path

    def safe(canvas, shape):
        try:
            if canvas.beginPath() is None:
                return None
        except Exception:
            return None
        try:
            return orig(canvas, shape)
        except Exception:
            return None

    svgmod._shape_to_pdf_path = safe
    svgmod._clip_patched = True


def render_svg(path, height_px: int, flatten_gradients: bool = False) -> Image.Image:
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg

    _patch_svglib_clip()
    raw = Path(path).read_bytes()

    if flatten_gradients:
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"url\(#[^)]*\)", "#FFFFFF", text)
        text = re.sub(r"<\?xml[^>]*\?>", "", text)   # 去掉声明，避免 lxml 报 encoding 声明错误
        src = io.StringIO(text)
    else:
        src = io.BytesIO(raw)                        # 走 bytes，lxml 才认 XML 声明
    d = svg2rlg(src)
    if d is None or not d.width or not d.height:
        raise RuntimeError("SVG 解析失败")
    s = height_px / float(d.height)
    d.scale(s, s)
    d.width *= s
    d.height *= s
    buf = io.BytesIO()
    renderPM.drawToFile(d, buf, fmt="PNG", bg=0xFFFFFF)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def load_logo(path: Path, height_px: int, color: str = "#1a1a1a",
              seal: bool = False) -> Image.Image:
    """返回高度为 height_px 的 logo。seal=True 表示完整色标（保留原色、不抠底）。"""
    path = Path(path)
    work_h = max(height_px * 3, 900)
    if path.suffix.lower() == ".svg":
        im = render_svg(path, work_h, flatten_gradients=seal)
    else:
        im = Image.open(path).convert("RGBA")
        if im.height != work_h:
            im = im.resize((max(1, round(im.width * work_h / im.height)), work_h), Image.LANCZOS)

    if seal:
        im = im.convert("RGB")
        mask = im.convert("L").point(lambda v: 255 if v < 250 else 0)
        bb = mask.getbbox()
        if bb:
            im = im.crop(bb)
        return im.resize((max(1, round(im.width * height_px / im.height)), height_px),
                         Image.LANCZOS).convert("RGBA")

    # 白底/浅底 → 透明：用"离白有多远"算覆盖度（彩色 logo 也能均匀变单色）
    from PIL import ImageChops
    r, g, b = im.convert("RGB").split()
    inv = [ch.point(lambda v: 255 - v) for ch in (r, g, b)]
    far = ImageChops.lighter(ImageChops.lighter(inv[0], inv[1]), inv[2])
    alpha = far.point(lambda v: 0 if v < 6 else (255 if v > 150 else int((v - 6) * 255 / 144)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.putalpha(alpha)
    bb = alpha.getbbox()
    if bb:
        out = out.crop(bb)
    solid = Image.new("RGBA", out.size, color)
    solid.putalpha(out.getchannel("A"))
    return solid.resize((max(1, round(solid.width * height_px / solid.height)), height_px),
                        Image.LANCZOS)


def find_logo(logo_dir: Path, brand: str):
    """按品牌找 logo，返回 (path, is_seal) 或 (None, False)。"""
    if not logo_dir or not Path(logo_dir).is_dir():
        return None, False
    d = Path(logo_dir)
    for name, seal in ((f"{brand}-seal.svg", True), (f"{brand}-seal.png", True),
                       (f"{brand}-wordmark.png", False), (f"{brand}-wordmark.svg", False),
                       (f"{brand}-logo.png", False), (f"{brand}-logo.svg", False),
                       (f"{brand}.png", False), (f"{brand}.svg", True),
                       (f"{brand}.jpg", False), (f"{brand}.webp", False)):
        p = d / name
        if p.exists():
            return p, seal
    return None, False


# ------------------------------------------------------------------ 排版

@dataclass
class Options:
    border: float = 0.035        # 白边（占短边）
    scale: float = 1.0           # 文字整体缩放
    template: str = "{focal} · {aperture} · {shutter} · {iso}"
    show_date: bool = True
    show_lens: bool = True
    show_meta: bool = True
    show_brand: bool = True
    seal_scale: float = 1.5      # 色标高度 = 文字块高度 × 该值
    logo_scale: float = 0.52     # 字标高度 = 文字块高度 × 该值
    color: str = "#141414"
    sub_color: str = "#575757"
    sub2_color: str = "#8f8f8f"
    brand_color: str = "#1a1a1a"
    model_override: str = ""
    lens_override: str = ""


def put(d, xy, s, font, fill, tracking=0.0):
    bb = d.textbbox((0, 0), s, font=font)
    x, y = xy[0] - bb[0], xy[1] - bb[1]
    if tracking:
        cx = x
        for ch in s:
            d.text((cx, y), ch, font=font, fill=fill)
            cx += d.textlength(ch, font=font) + tracking
    else:
        d.text((x, y), s, font=font, fill=fill)


def text_w(d, s, font, tracking=0.0):
    if not s:
        return 0
    if not tracking:
        return d.textlength(s, font=font)
    return sum(d.textlength(c, font=font) for c in s) + tracking * (len(s) - 1)


def render(im: Image.Image, meta: dict, opts: Options, logo_img: Image.Image | None = None,
           logo_is_seal: bool = False) -> Image.Image:
    """im 需已转置、RGB。返回加了白边和徽章的新图。"""
    brand_key = meta.get("brand", "unknown")
    b = BRANDS.get(brand_key, BRANDS["unknown"])

    if opts.model_override.strip():
        model = opts.model_override.strip()
    else:
        model = norm_model(brand_key, meta.get("raw_model", "")) or meta.get("raw_model", "")
    model = model or "Unknown"
    title = model if (b["name"] and model.lower().startswith(b["name"].lower())) else f"{b['name']} {model}".strip()

    lensline = "" if not opts.show_lens else (opts.lens_override.strip() or meta.get("lens", ""))
    params = opts.template.format(**meta).strip()
    params = re.sub(r"\s*·\s*(·\s*)+", " · ", params).strip(" ·")
    if not opts.show_meta:
        params = ""
    metaline = " · ".join(x for x in (params, meta.get("date", "") if opts.show_date else "") if x)

    W, H = im.size
    short = min(W, H)
    margin = max(6, int(round(short * opts.border)))

    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    ts = max(10, int(round(short * 0.021 * opts.scale)))

    def measure(size):
        f1 = font_for("bold", size)
        f2 = font_for("reg", max(8, int(round(size * 0.62))))
        f3 = font_for("reg", max(8, int(round(size * 0.55))))
        w = max(text_w(probe, title, f1),
                text_w(probe, lensline, f2) if lensline else 0,
                text_w(probe, metaline, f3) if metaline else 0)
        return f1, f2, f3, w

    while ts > 9:
        f1, f2, f3, left_w = measure(ts)
        fs = font_for("bold", max(10, int(round(ts * 1.12))), b["style"])
        mark_w = text_w(probe, b["mark"], fs, b["track"] * ts) if b["mark"] else 0
        if left_w + mark_w + ts * 2.0 <= W or not b["mark"]:
            break
        ts = int(ts * 0.94)

    f1, f2, f3, left_w = measure(ts)
    b1 = probe.textbbox((0, 0), title, font=f1)
    h1 = b1[3] - b1[1]
    h2 = h3 = 0
    if lensline:
        bb = probe.textbbox((0, 0), lensline, font=f2)
        h2 = bb[3] - bb[1]
    if metaline:
        bb = probe.textbbox((0, 0), metaline, font=f3)
        h3 = bb[3] - bb[1]
    gap = int(round(ts * 0.50))
    block_h = h1 + (gap + h2 if lensline else 0) + (gap + h3 if metaline else 0)

    pad_top = int(round(margin * 0.95))
    pad_bottom = int(round(margin * 1.15))

    if logo_img is not None:
        sc = opts.seal_scale if logo_is_seal else opts.logo_scale
        target_h = max(8, int(round(block_h * sc)))
        logo_img = logo_img.resize(
            (max(1, round(logo_img.width * target_h / logo_img.height)), target_h), Image.LANCZOS)
        max_w = int(W * 0.45)                 # 超宽字标（哈苏那种）不要溢出画面
        if logo_img.width > max_w:
            nh = max(8, round(logo_img.height * max_w / logo_img.width))
            logo_img = logo_img.resize((max_w, nh), Image.LANCZOS)

    inner_h = max(block_h, logo_img.height if logo_img is not None else 0)
    band = pad_top + inner_h + pad_bottom

    canvas = Image.new("RGB", (W + margin * 2, H + margin + band), "white")
    canvas.paste(im, (margin, margin))
    d = ImageDraw.Draw(canvas)

    band_top = margin + H + pad_top
    x = margin
    y = band_top + (inner_h - block_h) // 2

    put(d, (x, y), title, f1, opts.color)
    y += h1
    if lensline:
        y += gap
        put(d, (x, y), lensline, f2, opts.sub_color)
        y += h2
    if metaline:
        y += gap
        put(d, (x, y), metaline, f3, opts.sub2_color)

    if logo_img is not None:
        canvas.paste(logo_img, (margin + W - logo_img.width,
                                band_top + (inner_h - logo_img.height) // 2), logo_img)
    elif b["mark"] and opts.show_brand:
        fs = font_for("bold", max(10, int(round(ts * 1.12))), b["style"])
        mw = text_w(d, b["mark"], fs, b["track"] * ts)
        bb = d.textbbox((0, 0), b["mark"], font=fs)
        mh = bb[3] - bb[1]
        put(d, (margin + W - mw, band_top + (inner_h - mh) // 2), b["mark"], fs,
            opts.brand_color, b["track"] * ts)
    return canvas


# ------------------------------------------------------------------ 工具

def load_image(path) -> Image.Image:
    with Image.open(path) as im:
        meta = read_meta(im)
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
    return im


def estimate_kb(im: Image.Image, quality: int) -> float:
    """用中心裁块估全图 JPEG 体积（KB）。"""
    w, h = im.size
    side = min(1200, min(w, h))
    left = (w - side) // 2
    top = (h - side) // 2
    crop = im.crop((left, top, left + side, top + side))
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=int(quality), subsampling=0, optimize=True)
    per_px = buf.tell() / (side * side)
    return per_px * w * h / 1024


def save_jpeg(im: Image.Image, dst: Path, quality: int):
    im.save(dst, "JPEG", quality=int(quality), subsampling=0, optimize=True, progressive=True)
