# 维护笔记

给未来的自己：换作者、改 README、发版怎么弄。

---

## 一、作者信息（已填好，以后要改就改这几处）

当前作者：**AshClear**（<https://github.com/AshClear>）

| 位置 | 现在写的 |
|---|---|
| `README.md` 顶部链接 / 徽章 / Releases / Issues | `https://github.com/AshClear/Eazy-Watermarker` |
| `README.md` 作者段 | AshClear + 主页链接 |
| `README.md` 许可证段、`LICENSE` | `Copyright (c) 2026 AshClear` |
| `README.en.md` | 同上（英文） |

以后换账号或换人，全局替换 `AshClear` 即可：

```powershell
cd D:\Z63\修改图\Eazy-Watermarker
(Get-Content README.md -Raw)     -replace 'AshClear','新ID' | Set-Content README.md -NoNewline
(Get-Content README.en.md -Raw)  -replace 'AshClear','新ID' | Set-Content README.en.md -NoNewline
(Get-Content LICENSE -Raw)       -replace 'AshClear','新ID' | Set-Content LICENSE -NoNewline
```

> 仓库 URL 里的 `Eazy-Watermarker` 如果也改了，记得一起替换。

### 关于 AI 辅助

README 里**不写**这一段（作者觉得放在主页上别扭），协作方式记录在
[`AGENTS.md`](../AGENTS.md) 的约定里；需要对外说明时，写在 Issue 回复或 Release 说明中即可。

### Git 提交身份

```powershell
git config --global user.name  "你的名字"
git config --global user.email "you@example.com"
```

已提交想改作者：

```powershell
git commit --amend --reset-author --no-edit
```

---

## 二、README 的结构与哪块该改什么

现在 README 是「项目主页」式排版（参考 Ncrust 那种写法），从上到下：

| 区块 | 什么时候动 |
|---|---|
| 标题 / 一句话定位 | 定位变了才动 |
| 徽章（version / exe 体积 / license） | **每次发版**改 version，exe 体积变了改数字 |
| 顶部链接行 | 换仓库名 / 域名时 |
| ⚠️ 说明 | 政策变了（比如开始收集统计）才动 |
| 为什么是 Eazy Watermarker（特性表） | 加了大功能就补一行 |
| 功能一览 | 同上 |
| 三种用法 | 命令变了要同步（`src/` 路径改了务必改这里） |
| 品牌标志 | 命名规则 / fetch 脚本参数变了要改 |
| 参数表 | **`core.Options` 默认值变了必须改** |
| 从源码构建 | `build.bat` / PyInstaller 参数变了要改 |
| 版本历史 | 每次发版加一行 |
| 关于 AI 辅助 | 协作方式变了再改 |
| Star History | 换成你的账号后就不用管了 |

### 改 README 的两种方式

**A. GitHub 网页**：仓库首页点 `README.md` → 右上角铅笔 → 改 → `Commit changes`。
适合改错别字、补 FAQ。

**B. 本地改**：

```powershell
git add README.md
git commit -m "docs: 更新参数表"
git push
```

本地预览 Markdown：VS Code 里 `Ctrl+Shift+V`。

---

## 三、发版流程

```powershell
# 1. 改 README 的版本徽章 + 版本历史表
# 2. 提交
git add -A
git commit -m "chore: release v1.0.1"

# 3. 打标签并推送
git tag v1.0.1
git push origin main --tags
```

打 tag 后 `.github/workflows/build.yml` 会自动：

1. windows-latest 上编译 `EazyWatermarker.exe`
2. 打包网页版 `web.zip`
3. 建 Release 并挂上这两个附件

普通 push 只跑自检（编译检查 + 网页构建 + CLI 冒烟），不发版。

---

## 四、维护约定

1. **`logos/*.svg` 不提交** —— 商标问题，`.gitignore` 已挡。
2. **`dist/`、`*.exe` 不提交** —— 走 Release。
3. **截图用合成图** —— `docs/demo.jpg` 是脚本生成的，不含他人照片和品牌 logo。
4. **改完跑自检**（见 [AGENTS.md](../AGENTS.md)）。
5. 提交信息用 `feat:` / `fix:` / `docs:` / `chore:`。

---

## 五、想加功能时改哪里

| 想改什么 | 改哪个文件 |
|---|---|
| 版式（白边比例、行距、标识位置） | `src/core.py` → `Options` 与 `render()` |
| 品牌识别 / 机型归一化 | `src/core.py` → `BRAND_KEYS`、`norm_model()` |
| 新增品牌下拉候选 | `src/core.py` → `COMMON_MODELS` |
| 桌面版界面 | `src/gui.py` |
| 网页版界面 | `src/web_template.html`（算法要与 `core.py` 同步） |
| 命令行参数 | `src/cli.py` |
| 标志下载清单 | `src/fetch_logos.py` → `CATALOG` |
