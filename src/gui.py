#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
品牌水印工具 —— 桌面版（tkinter）

功能：
  · 读取 EXIF，自动识别品牌 / 机型 / 镜头 / 参数 / 时间
  · 白边 + 左下角机型·镜头·参数，右下角品牌标识
  · 品牌标志可自行导入（SVG / PNG），按品牌自动匹配
  · 机型可下拉选择，也可手动输入
  · 输出质量可调，并给出预计体积
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import core

APP_NAME = "Eazy Watermarker"
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
PREVIEW_MAX = 1100


def app_dir() -> Path:
    """exe 或脚本所在目录（打包后 logo 放在 exe 旁边）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def ensure_logos(dst: Path):
    """打包版首次运行时，把内置标志释放到 exe 旁边的 logos/。"""
    if not getattr(sys, "frozen", False):
        return
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "logos"
    if not bundled.is_dir():
        return
    import shutil
    dst.mkdir(parents=True, exist_ok=True)
    for f in bundled.iterdir():
        if f.is_file() and not (dst / f.name).exists():
            shutil.copy2(f, dst / f.name)


def run_selftest() -> int:
    """命令行自检：验证 EXIF / logo（含 SVG 栅格化）/ 排版 是否正常。"""
    from PIL import ImageDraw

    logo_dir = app_dir() / "logos"
    print("app_dir:", app_dir())
    print("logo_dir:", logo_dir, "exists:", logo_dir.is_dir())

    path, seal = core.find_logo(logo_dir, "nikon")
    print("logo:", path, "seal:", seal, flush=True)
    lg = core.load_logo(path, 400, seal=seal) if path else None
    print("logo size:", lg.size if lg else None, flush=True)

    im = Image.new("RGB", (1200, 800), (60, 90, 120))
    d = ImageDraw.Draw(im)
    d.rectangle((60, 60, 1140, 740), outline=(220, 220, 220), width=4)
    meta = core.read_meta(im)
    meta.update(brand="nikon", raw_model="NIKON Z6_3", lens="NIKKOR Z 24-120mm f/4 S",
                focal="24mm", aperture="f/8", shutter="1/640s", iso="ISO100",
                date="2026-11-24 14:27")
    out = core.render(im, meta, core.Options(), lg, seal)
    dst = app_dir() / "_selftest.jpg"
    core.save_jpeg(out, dst, 90)
    print("rendered:", out.size, "->", dst, dst.stat().st_size // 1024, "KB")
    print("SELFTEST OK")
    return 0


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1300, sw - 80), min(860, sh - 120)
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{max(0, (sh - h)//2 - 40)}")
        self.minsize(1080, 680)
        self._dpi()

        self.logo_dir = app_dir() / "logos"
        self.logo_dir.mkdir(parents=True, exist_ok=True)

        self.files: list[Path] = []
        self.cur = 0
        self.meta: dict = {}
        self.src_path: Path | None = None
        self.full_img: Image.Image | None = None
        self.preview_base: Image.Image | None = None
        self._preview_job = None
        self._tkimg = None
        self.auto_model = True
        self.auto_lens = True

        self._build_ui()
        self._refresh_logo_list()

    # ------------------------------------------------------------- UI
    def _dpi(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        try:
            dpi = self.winfo_fpixels("1i")
            self.tk.call("tk", "scaling", dpi / 72.0)
        except Exception:
            pass

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass

        root = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)

        # 左：文件列表
        left = ttk.Frame(root, width=260)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        ttk.Label(left, text="照片列表", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        lf = ttk.Frame(left)
        lf.pack(fill="both", expand=True, pady=4)
        self.lst = tk.Listbox(lf, activestyle="none", exportselection=False)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.lst.yview)
        self.lst.configure(yscrollcommand=sb.set)
        self.lst.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.lst.bind("<<ListboxSelect>>", self._on_select)

        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=4)
        ttk.Button(bar, text="添加照片", command=self.add_files).pack(side="left")
        ttk.Button(bar, text="添加文件夹", command=self.add_folder).pack(side="left", padx=4)
        ttk.Button(bar, text="清空", command=self.clear_files).pack(side="left")

        # 中：预览
        mid = ttk.Frame(root)
        mid.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(mid, bg="#e9e9e9", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.schedule_preview())
        self.info = ttk.Label(mid, text="拖入照片或点左侧「添加照片」", anchor="w")
        self.info.pack(fill="x", pady=(4, 0))

        # 右：参数
        right = ttk.Frame(root, width=330)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)
        self._build_options(right)

    def _build_options(self, parent):
        pad = dict(padx=6, pady=3)

        ttk.Label(parent, text="品牌 / 机型", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        box = ttk.LabelFrame(parent, padding=8)
        box.pack(fill="x", pady=(2, 8))

        self.brand_var = tk.StringVar(value="自动")
        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="品牌", width=6).pack(side="left")
        self.brand_values = ["自动"] + [core.BRANDS[k]["name"] for k in core.BRANDS
                                        if k != "unknown" and core.BRANDS[k]["name"]]
        self.brand_cb = ttk.Combobox(row, textvariable=self.brand_var, width=16, state="readonly",
                                     values=self.brand_values)
        self.brand_cb.pack(side="left")
        self.brand_cb.bind("<<ComboboxSelected>>", lambda e: self.on_brand_change())

        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="机型", width=6).pack(side="left")
        self.model_var = tk.StringVar()
        self.model_cb = ttk.Combobox(row, textvariable=self.model_var, width=16)
        self.model_cb.pack(side="left", fill="x", expand=True)
        self.model_var.trace_add("write", lambda *a: self._model_typed())
        ttk.Button(row, text="自动", width=5, command=self.reset_auto_model).pack(side="left", padx=(4, 0))

        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="镜头", width=6).pack(side="left")
        self.lens_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.lens_var, width=22).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="自动", width=5, command=self.reset_auto_lens).pack(side="left", padx=(4, 0))

        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="参数", width=6).pack(side="left")
        self.tpl_var = tk.StringVar(value="{focal} · {aperture} · {shutter} · {iso}")
        ttk.Entry(row, textvariable=self.tpl_var, width=22).pack(side="left", fill="x", expand=True)

        self.show_lens = tk.BooleanVar(value=True)
        self.show_meta = tk.BooleanVar(value=True)
        self.show_date = tk.BooleanVar(value=True)
        self.show_brand = tk.BooleanVar(value=True)
        row = ttk.Frame(box)
        row.pack(fill="x", pady=(6, 0))
        for text, var in (("镜头", self.show_lens), ("参数", self.show_meta),
                          ("日期", self.show_date), ("标识", self.show_brand)):
            ttk.Checkbutton(row, text=text, variable=var,
                            command=self.schedule_preview).pack(side="left", padx=(0, 8))

        # 版式
        ttk.Label(parent, text="版式", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        box2 = ttk.LabelFrame(parent, padding=8)
        box2.pack(fill="x", pady=(2, 8))

        self.border_var = tk.DoubleVar(value=3.5)
        self.scale_var = tk.DoubleVar(value=1.0)
        self.seal_var = tk.DoubleVar(value=150)

        for label, var, lo, hi, unit in (
            ("白边 %", self.border_var, 0.5, 10.0, "%"),
            ("字号 %", self.scale_var, 50, 200, "%"),
            ("标识大小 %", self.seal_var, 60, 260, "%"),
        ):
            row = ttk.Frame(box2)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=9).pack(side="left")
            ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal",
                      command=lambda *_: self.schedule_preview()).pack(side="left", fill="x", expand=True)
            val = ttk.Label(row, width=6, anchor="e")
            val.pack(side="left")
            var.trace_add("write", lambda *a, v=var, l=val, u=unit: l.configure(text=f"{v.get():.0f}{u}"))

        # 输出
        ttk.Label(parent, text="输出", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        box3 = ttk.LabelFrame(parent, padding=8)
        box3.pack(fill="x", pady=(2, 8))

        row = ttk.Frame(box3)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="质量", width=9).pack(side="left")
        self.q_var = tk.DoubleVar(value=92)
        ttk.Scale(row, from_=60, to=100, variable=self.q_var, orient="horizontal",
                  command=lambda *_: self.update_estimate()).pack(side="left", fill="x", expand=True)
        self.q_lbl = ttk.Label(row, width=6, anchor="e", text="92")
        self.q_lbl.pack(side="left")
        self.q_var.trace_add("write", lambda *a: self.q_lbl.configure(text=f"{self.q_var.get():.0f}"))

        self.est_lbl = ttk.Label(box3, text="预计大小：—", foreground="#666")
        self.est_lbl.pack(anchor="w", pady=(2, 0))

        row = ttk.Frame(box3)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="导出当前", command=self.export_current).pack(side="left")
        ttk.Button(row, text="导出全部", command=self.export_all).pack(side="left", padx=6)
        ttk.Button(row, text="输出目录…", command=self.pick_outdir).pack(side="left")

        self.outdir_var = tk.StringVar(value="")
        ttk.Label(box3, textvariable=self.outdir_var, foreground="#888", wraplength=300).pack(anchor="w")

        # 品牌标识
        ttk.Label(parent, text="品牌标识", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        box4 = ttk.LabelFrame(parent, padding=8)
        box4.pack(fill="both", expand=True, pady=(2, 0))
        lf = ttk.Frame(box4)
        lf.pack(fill="both", expand=True)
        self.logo_lst = tk.Listbox(lf, height=5, activestyle="none")
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.logo_lst.yview)
        self.logo_lst.configure(yscrollcommand=sb.set)
        self.logo_lst.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        row = ttk.Frame(box4)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="导入标志…", command=self.import_logo).pack(side="left")
        ttk.Button(row, text="删除", command=self.remove_logo).pack(side="left", padx=4)
        ttk.Label(box4, text="支持 SVG / PNG，透明底最好；文件名按品牌命名（如 sony.svg）",
                  foreground="#888", wraplength=300).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------- 文件
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择照片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp"), ("所有文件", "*.*")],
        )
        self._append([Path(p) for p in paths])

    def add_folder(self):
        d = filedialog.askdirectory(title="选择文件夹")
        if not d:
            return
        files = sorted(p for p in Path(d).iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT)
        self._append(files)

    def _append(self, paths):
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.lst.insert("end", p.name)
        if self.files and self.src_path is None:
            self.lst.selection_set(0)
            self.load_index(0)

    def clear_files(self):
        self.files.clear()
        self.lst.delete(0, "end")
        self.src_path = None
        self.meta = {}
        self.full_img = None
        self.preview_base = None
        self.canvas.delete("all")
        self.info.configure(text="拖入照片或点左侧「添加照片」")
        self.est_lbl.configure(text="预计大小：—")

    def _on_select(self, _evt=None):
        sel = self.lst.curselection()
        if sel:
            self.load_index(sel[0])

    def load_index(self, i: int):
        if not (0 <= i < len(self.files)):
            return
        self.cur = i
        self.src_path = self.files[i]
        with Image.open(self.src_path) as im0:
            self.meta = core.read_meta(im0)
        self.full_img = core.load_image(self.src_path)

        if self.brand_var.get() in ("自动", ""):
            self._sync_brand_ui()
        else:
            self._apply_brand_override()

        if self.auto_model:
            self.auto_model = True
            self.model_var.set(self.model_display())
        self.model_cb.configure(values=self.model_values())
        if self.auto_lens:
            self.lens_var.set(self.meta.get("lens", ""))

        self.preview_base = self.full_img.copy()
        self.preview_base.thumbnail((PREVIEW_MAX, PREVIEW_MAX), Image.LANCZOS)
        self.update_estimate()
        self.schedule_preview()

    def _sync_brand_ui(self):
        name = core.BRANDS.get(self.meta.get("brand", "unknown"), {}).get("name") or "自动"
        self.brand_var.set(name)

    def _apply_brand_override(self):
        name = self.brand_var.get()
        if name in ("自动", ""):
            self._sync_brand_ui()
            return
        for k, v in core.BRANDS.items():
            if v["name"] == name:
                self.meta["brand"] = k
                break
        self.model_cb.configure(values=self.model_values())

    def on_brand_change(self):
        self._apply_brand_override()
        if self.auto_model:
            self.model_var.set(self.model_display())
        self.schedule_preview()

    def model_values(self):
        b = self.meta.get("brand", "unknown")
        return core.COMMON_MODELS.get(b, [])

    def model_display(self):
        b = self.meta.get("brand", "unknown")
        return core.norm_model(b, self.meta.get("raw_model", "")) or self.meta.get("raw_model", "")

    def _model_typed(self):
        if self.model_var.get() != self.model_display():
            self.auto_model = False
        self.schedule_preview()

    def reset_auto_model(self):
        self.auto_model = True
        self.model_var.set(self.model_display())
        self.schedule_preview()

    def reset_auto_lens(self):
        self.auto_lens = True
        self.lens_var.set(self.meta.get("lens", ""))
        self.schedule_preview()

    # ------------------------------------------------------------- 选项
    def options(self) -> core.Options:
        o = core.Options()
        o.border = max(0.003, self.border_var.get() / 100.0)
        o.scale = self.scale_var.get() / 100.0
        o.seal_scale = self.seal_var.get() / 100.0
        o.logo_scale = o.seal_scale * 0.35
        o.template = self.tpl_var.get()
        o.show_lens = self.show_lens.get()
        o.show_meta = self.show_meta.get()
        o.show_date = self.show_date.get()
        o.show_brand = self.show_brand.get()
        if not self.auto_model:
            o.model_override = self.model_var.get()
        if not self.auto_lens:
            o.lens_override = self.lens_var.get()
        return o

    def current_logo(self):
        brand = self.meta.get("brand", "unknown")
        path, seal = core.find_logo(self.logo_dir, brand)
        if not path:
            return None, False
        try:
            return core.load_logo(path, 600, seal=seal), seal
        except Exception:
            return None, False

    # ------------------------------------------------------------- 预览
    def schedule_preview(self):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(120, self.draw_preview)

    def draw_preview(self):
        self._preview_job = None
        if self.preview_base is None:
            return
        try:
            lg, seal = self.current_logo()
            out = core.render(self.preview_base, self.meta, self.options(), lg, seal)
        except Exception as e:
            self.info.configure(text=f"预览失败：{e}")
            return

        cw = max(self.canvas.winfo_width(), 200) - 16
        ch = max(self.canvas.winfo_height(), 200) - 16
        view = out.copy()
        view.thumbnail((cw, ch), Image.LANCZOS)

        self._tkimg = ImageTk.PhotoImage(view)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2 + 8, ch // 2 + 8, image=self._tkimg, anchor="center")

        m = self.meta
        self.info.configure(
            text=f"{self.src_path.name}   ·   {m.get('make','')} {m.get('raw_model','')}"
                 f"   ·   {m.get('lens','')}   ·   {out.size[0]}×{out.size[1]}")

    def update_estimate(self):
        if self.full_img is None:
            return
        try:
            q = int(self.q_var.get())
            W, H = self.full_img.size
            base = core.estimate_kb(self.full_img, q)
            # 加上白边和底栏带来的面积增量
            border = max(0.003, self.border_var.get() / 100.0)
            m = min(W, H) * border
            extra = ((W + 2 * m) * (H + m + 3 * m)) / (W * H)
            kb = base * extra
            self.est_lbl.configure(text=f"预计大小：约 {kb/1024:.1f} MB（原图 "
                                        f"{self.src_path.stat().st_size/1024/1024:.1f} MB）")
        except Exception:
            self.est_lbl.configure(text="预计大小：—")

    # ------------------------------------------------------------- 导出
    def pick_outdir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.outdir_var.set(d)

    def _export_one(self, p: Path, out_dir: Path, q: int, opts: core.Options, logo_dir: Path,
                    meta: dict | None = None) -> Path:
        im = core.load_image(p)
        meta = meta if meta is not None else self._meta_of(p)
        path, seal = core.find_logo(logo_dir, meta.get("brand", "unknown"))
        lg = None
        if path:
            try:
                lg = core.load_logo(path, 600, seal=seal)
            except Exception:
                lg = None
        out = core.render(im, meta, opts, lg, seal)
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / f"{p.stem}_wm.jpg"
        core.save_jpeg(out, dst, q)
        return dst

    def _meta_of(self, p: Path) -> dict:
        with Image.open(p) as im:
            return core.read_meta(im)

    def _out_dir_for(self, p: Path) -> Path:
        d = self.outdir_var.get().strip()
        return Path(d) if d else (p.parent / "framed")

    def export_current(self):
        if not self.files:
            return
        q = int(self.q_var.get())
        p = self.files[self.cur]
        try:
            dst = self._export_one(p, self._out_dir_for(p), q, self.options(), self.logo_dir,
                                   dict(self.meta))
            self.info.configure(text=f"已导出：{dst}")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"导出失败：{e}")

    def export_all(self):
        if not self.files:
            return
        q = int(self.q_var.get())
        files = list(self.files)
        opts = self.options()          # 在主线程快照，避免子线程碰 Tk 变量
        logo_dir = self.logo_dir
        out_override = self.outdir_var.get().strip()
        self.info.configure(text="正在导出…")

        def work():
            ok = 0
            errs = []
            for i, p in enumerate(files, 1):
                try:
                    out_dir = Path(out_override) if out_override else (p.parent / "framed")
                    self._export_one(p, out_dir, q, opts, logo_dir)
                    ok += 1
                except Exception as e:
                    errs.append(f"{p.name}: {e}")
                self.after(0, lambda i=i: self.info.configure(text=f"正在导出 {i}/{len(files)}…"))
            msg = f"完成 {ok}/{len(files)} 张"
            if errs:
                msg += "\n\n失败：\n" + "\n".join(errs[:8])
            self.after(0, lambda: (self.info.configure(text=msg), messagebox.showinfo(APP_NAME, msg)))

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------- 标志
    def _refresh_logo_list(self):
        self.logo_lst.delete(0, "end")
        if not self.logo_dir.exists():
            return
        for p in sorted(self.logo_dir.iterdir()):
            if p.suffix.lower() in {".svg", ".png", ".jpg", ".webp"}:
                self.logo_lst.insert("end", p.name)

    def import_logo(self):
        p = filedialog.askopenfilename(
            title="选择品牌标志（建议透明 PNG 或 SVG）",
            filetypes=[("标志文件", "*.svg *.png *.jpg *.jpeg *.webp"), ("所有文件", "*.*")],
        )
        if not p:
            return
        src = Path(p)
        brands = [k for k in core.BRANDS if k != "unknown"]
        dlg = tk.Toplevel(self)
        dlg.title("这是哪个品牌？")
        dlg.transient(self)
        dlg.grab_set()
        ttk.Label(dlg, text=f"{src.name}\n绑定到哪个品牌？", padding=12).pack()
        var = tk.StringVar(value=self.meta.get("brand", "nikon"))
        cb = ttk.Combobox(dlg, textvariable=var, state="readonly",
                          values=[f"{core.BRANDS[k]['name'] or k} ({k})" for k in brands], width=28)
        cb.pack(padx=12)
        cb.current(brands.index(var.get()) if var.get() in brands else 0)

        def okay():
            idx = cb.current()
            key = brands[idx]
            suffix = src.suffix.lower()
            for old in self.logo_dir.glob(f"{key}.*"):
                old.unlink()
            dst = self.logo_dir / f"{key}{suffix}"
            dst.write_bytes(src.read_bytes())
            self._refresh_logo_list()
            dlg.destroy()
            self.schedule_preview()

        ttk.Button(dlg, text="确定", command=okay).pack(pady=12)

    def remove_logo(self):
        sel = self.logo_lst.curselection()
        if not sel:
            return
        name = self.logo_lst.get(sel[0])
        (self.logo_dir / name).unlink(missing_ok=True)
        self._refresh_logo_list()
        self.schedule_preview()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(run_selftest())
    ensure_logos(app_dir() / "logos")
    App().mainloop()
