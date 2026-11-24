# Eazy Watermarker

### 把相机参数，印成一张能发出去的卡片

**离线 · 不上传 · 读 EXIF 自动配品牌**

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](https://github.com/AshClear/Eazy-Watermarker/releases)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Browser-0078D4)](https://github.com/AshClear/Eazy-Watermarker/releases)
[![EXE](https://img.shields.io/badge/exe-24.5%20MB-blue)](https://github.com/AshClear/Eazy-Watermarker/releases)
[![Offline](https://img.shields.io/badge/network-none-success)](#)

[**下载**](https://github.com/AshClear/Eazy-Watermarker/releases) · [**网页版**](#-三种用法) · [**品牌标志**](#-品牌标志) · [**问题反馈**](https://github.com/AshClear/Eazy-Watermarker/issues) · [维护笔记](docs/MAINTAINING.md)

> **⚠️ 说明**
>
> 照片只在本机处理，不联网、不上传。
>
> 仓库**不附带**任何品牌标志 —— 那是各家商标，请自行准备（脚本可代下）。
>
> 本工具只做排版，不修图；导出的是新文件，不会覆盖原图。

---

## 为什么是 Eazy Watermarker

> 加水印的工具很多，但大多要你一张张手填机型、手调边距、手对齐。Eazy Watermarker 把这一切交给 EXIF：**照片进来，卡片出去。**

| | |
|---|---|
| 🏷️ **认出你的机器** | 读 EXIF 的 Make / Model，`NIKON Z6_3` → `Z6III`，`ILCE-7CM2` → `α7C II`，`Canon EOS R6m2` → `EOS R6 Mark II` |
| 📐 **按比例排版** | 白边、字号、标识全部按短边百分比计算，4032px 和 1200px 出来是同一个版式 |
| 🔤 **三级信息层级** | 机型 / 镜头 / 参数 + 时间，三档字重与灰度，不抢画面 |
| 🖼️ **官方标志可选** | `<品牌>-seal` 保留原色完整标，`<品牌>-wordmark` 自动抠白底转单色 |
| 🧩 **缺标志也不空** | 没有对应文件时用文字字标（NIKON / SONY / Canon …），版式不变 |
| 🎚️ **体积心里有数** | 质量 60–100 滑块，旁边直接给**预估 MB** 和输出尺寸 |
| 💻 **三种形态** | Windows exe、单文件离线网页、命令行批量 —— 同一套排版代码 |
| 🚫 **零上传** | 没有服务器、没有账号、没有遥测 |

---

## ✨ 功能一览

### 🖼️ 排版

- **白边**：四边等宽，默认短边 3.5%，滑块 0.5%–10%
- **文字块**：左下角三行 —— 机型（黑，粗） / 镜头（中灰） / 参数+时间（浅灰）
- **品牌位**：右下角，与文字块垂直居中，完整标或字标自动切换
- **自适应**：文字过长自动缩字号；超宽字标限宽 45% 画面，不溢出
- **开关**：镜头 / 参数 / 日期 / 标识 可单独关闭

### 🏷️ 品牌

- 按 EXIF `Make` 自动映射 14 个品牌：Nikon、Sony、Canon、Fujifilm、Lumix、OM System、Leica、Pentax、Ricoh、Hasselblad、DJI、Sigma、Apple、Google
- 机型归一化覆盖各家命名差异（`Z6_3` / `ILCE-` / `EOS R6m2` / `DC-S5M2` …）
- 机型可手动输入，也可从下拉候选里挑

### 📤 输出

- JPEG 质量 60–100，4:4:4 无色度抽样
- 预估体积（中心取样 × 面积换算，误差约 ±20%）
- 批量：整文件夹一次跑完，输出到 `framed/`

---

## 📦 三种用法

### 1️⃣ Windows exe（免安装）

从 [Releases](https://github.com/AshClear/Eazy-Watermarker/releases) 下载 `EazyWatermarker.exe`，双击即用。
首次运行会在 exe 旁边生成 `logos\`，把品牌标志丢进去即可。

### 2️⃣ 网页版（单文件离线）

```bash
python src/make_web.py
```

生成 `build/web/index.html`，双击用 Chrome / Edge 打开。拖图、调参、导出，全程不出浏览器。
标志在构建时**内嵌**进 HTML，所以要先把文件放进 `logos/` 再生成。

### 3️⃣ 命令行

```bash
python src/cli.py 照片文件夹 -o 输出目录
python src/cli.py a.jpg -o out --quality 90 --border 4
python src/cli.py photos --brand sony --model "α7 IV" --seal 130
```

---

## 🏷️ 品牌标志

**仓库不附带任何标志文件**（商标问题）。三种用法：

**A. 什么都不做** —— 自动用文字字标，版式完全一致，不需要额外文件。

**B. 跑脚本下载**

```bash
python src/fetch_logos.py --list                     # 清单与可用来源
python src/fetch_logos.py --all                      # Wikimedia Commons 原件（14 个）
python src/fetch_logos.py --all --source jsdelivr    # 国内网络可直连（8 个）
python src/fetch_logos.py --only sony canon          # 只下指定品牌
python src/fetch_logos.py --all --dry-run            # 只打印地址
```

脚本会校验内容确实是 SVG（不是 404 页面 / 空文件）才落盘，重复运行不会覆盖已有文件。

| 源 | 覆盖 | 说明 |
|---|---|---|
| `commons`（默认） | 14 个品牌 | Wikimedia 矢量原件，质量最好；国内网络可能连不上 |
| `jsdelivr` | 8 个品牌 | Simple Icons，国内可直连；单色图标 |

**C. 自己放文件**

```
logos/
  nikon-seal.svg        完整标（带底色/图形），保留原色
  sony-wordmark.svg     字标，抠白底 → 透明 → 统一深灰
  canon-logo.svg        同 wordmark 的另一种写法
  fujifilm.svg          也认，按完整标处理
```

优先级：`<品牌>-seal.*` → `<品牌>-wordmark.*` → `<品牌>-logo.*` → `<品牌>.*`

来源清单见 [logos/SOURCES.md](logos/SOURCES.md)，命名规则见 [logos/README.md](logos/README.md)。

---

## ⚙️ 参数

| 参数 | 默认 | 范围 | 说明 |
|---|---|---|---|
| 白边 | 3.5% | 0.5%–10% | 占照片短边 |
| 字号 | 100% | 50%–200% | 机型/镜头/参数整体缩放 |
| 标识 | 150% | 60%–260% | 标识高度 = 文字块高度 × 该值 |
| 质量 | 92 | 60–100 | JPEG 质量 |

参数模板占位符：`{focal}` `{aperture}` `{shutter}` `{iso}` `{make}` `{lens}`

---

## 🛠️ 从源码构建

### 环境

Python 3.10+（用了 `str | None` 语法）

```bash
pip install -r requirements.txt
python src/gui.py
```

### 一条命令出全部产物（Windows）

```bat
build.bat
```

等价于：

```powershell
python src/make_web.py

python -m PyInstaller --onefile -w --name EazyWatermarker `
  --add-data "%CD%\logos;logos" `
  --collect-all svglib --collect-all rlPyCairo `
  --exclude-module numpy --exclude-module scipy --exclude-module pandas `
  --exclude-module matplotlib --exclude-module cv2 `
  --distpath dist --workpath build/pyi --specpath build/pyi `
  src/gui.py
```

产物：`build/web/index.html`、`dist/EazyWatermarker.exe`（约 24.5 MB）。

### 自检

```bash
python src/gui.py --selftest                     # EXIF + SVG + 排版，不开界面
python src/cli.py docs/demo.jpg -o build/out     # 命令行冒烟
```

CI（`.github/workflows/build.yml`）：每次 push 跑编译检查 + 网页构建 + CLI 冒烟；
打 `v*` 标签时在 windows-latest 上编译 exe 并自动发布 Release。

---

## 🧭 技术架构

| 主题 | 说明 |
|---|---|
| **排版引擎** | 所有尺寸 = 短边 × 比例，先量真实文字外框再算行高，字号在放不下时按 0.94 递减 |
| **机型归一化** | 每品牌一条规则：`Z6_3`→`Z6III`、`ILCE-7CM2`→`α7C II`、`R6m2`→`Mark II`、`DC-S5M2`→`S5 II` |
| **标志抠图** | 按「离白的距离」算 alpha（不是亮度），彩色 logo 才能均匀转单色；再裁外框、等比缩放 |
| **SVG 栅格化** | svglib + reportlab；给它打了两处补丁：clip 转换在 PNG 后端会崩、渐变填色会被丢弃 |
| **网页版** | 同一套版式用 Canvas 重写，自带精简 EXIF 解析（JPEG APP1 / PNG eXIf），无任何外部依赖 |
| **体积预估** | 中心 700–1200px 裁块按目标质量编码，按面积换算全图 |

```
src/
  core.py            EXIF、机型归一化、排版渲染、logo 处理、体积估算
  gui.py             tkinter 桌面版（含 --selftest）
  cli.py             命令行批量
  make_web.py        模板 + logos → 单文件 HTML
  fetch_logos.py     可选：按需下载品牌标志
  web_template.html  网页版（HTML + Canvas + JS）
```

---

## 📋 版本历史

| 版本 | 日期 | 亮点 |
|---|---|---|
| v1.0.0 | 2026-11 | 首个正式版：白边 + 三级文字 + 品牌标；exe / 网页 / CLI 三形态；EXIF 自动识别 14 品牌 |

---

## 📄 许可证

**MIT**，Copyright (c) 2026 AshClear。完整文本见 [LICENSE](LICENSE)。

作者：[AshClear](https://github.com/AshClear) · 品牌名称与标志归各自权利人所有，本仓库不附带。

---

[问题反馈](https://github.com/AshClear/Eazy-Watermarker/issues) · [维护笔记](docs/MAINTAINING.md) · [Releases](https://github.com/AshClear/Eazy-Watermarker/releases)
