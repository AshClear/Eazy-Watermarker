# AGENTS.md

给在这个仓库里干活的 AI / 协作者：改之前先读这页，能省掉一半返工。

## 项目是什么

一个**离线**照片排版工具：读 EXIF → 加白边 → 左下角机型/镜头/参数 → 右下角品牌标。
三种形态共用同一套排版逻辑：桌面版（tkinter）、网页版（Canvas）、命令行。

## 目录与职责

| 路径 | 职责 | 改动注意 |
|---|---|---|
| `src/core.py` | EXIF、机型归一化、排版、logo 处理、体积估算 | **所有形态的唯一真相**，改这里别在别处复制逻辑 |
| `src/gui.py` | tkinter 界面 | 只负责收集参数、调 `core.render()` |
| `src/cli.py` | 命令行 | 同上 |
| `src/make_web.py` | 模板 + logos → 单文件 HTML | 只做打包，不改渲染 |
| `src/web_template.html` | 网页版实现 | 与 `core.py` 的算法**必须同步**（见下） |
| `src/fetch_logos.py` | 下载品牌标志 | 只新增 `CATALOG` 条目，别改下载/校验逻辑 |

## 硬规则

1. **所有尺寸按短边比例**，不要出现写死的像素值。改版式时保证 1200px 和 6000px 的图出来是同一版。
2. **不要提交品牌标志**（`logos/*.svg|png` 已在 `.gitignore`）—— 商标问题。
3. **不要提交 `dist/`、`build/`、`*.exe`** —— 二进制走 Release。
4. **不要引入联网逻辑**到 `core/gui/cli`。只有 `fetch_logos.py` 允许联网，且必须是用户显式执行。
5. **不要重写 `core.render()` 的排版顺序**（机型 → 镜头 → 参数 → 标识），改之前先看 README 的版式图。

## 已知的坑（踩过）

- **svglib 两处补丁**（在 `core._patch_svglib_clip` 与 `render_svg`）：
  - `renderPM` 后端没有 `beginPath`，处理 clip 时会崩 → 补丁里兜成 `None`
  - SVG 里的渐变填色（`url(#grad)`）会被静默丢弃 → 需要时替换成纯色
- **SVG 的 XML 声明**：`svg2rlg(StringIO(带 encoding 声明的文本))` 会报错，必须走 `BytesIO(bytes)`。
- **彩色 logo 抠图**：不要用亮度算 alpha（Google 那种多色字标会花），用「离白的距离」。
- **超宽字标**（哈苏约 12.7:1）必须限宽，否则溢出画面。
- **打包 exe** 时 `--add-data` 的路径相对于 spec 目录，必须写绝对路径。

## 改完必须跑

```bash
python src/gui.py --selftest                  # EXIF + SVG + 排版
python src/cli.py docs/demo.jpg -o build/out  # 命令行
python src/make_web.py                        # 网页构建
```

网页版改动还要在浏览器里实际拖一张图、点导出，确认不是「能构建但跑不起来」。

## 提交信息

`feat:` / `fix:` / `docs:` / `chore:`，一句话说清改了什么。
涉及版式的改动，说明**改的是哪个比例参数**（例如「白边默认 3.5% → 3.2%」）。
