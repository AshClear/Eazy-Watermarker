# 把品牌标志放这里

文件名规则：`<品牌代号>-seal.svg` / `<品牌代号>-wordmark.svg` / `<品牌代号>.png`

```
nikon-seal.svg        完整标（带底色/图形），保留原色
sony-wordmark.svg     字标，自动抠白底 → 透明 → 统一深灰
canon-logo.svg        同 wordmark，另一种写法
fujifilm.svg          也认，按完整标处理
```

优先级：`<brand>-seal.*` → `<brand>-wordmark.*` → `<brand>-logo.*` → `<brand>.*`

支持品牌代号：

| 代号 | 对应 |
|---|---|
| `nikon` | Nikon |
| `sony` | Sony |
| `canon` | Canon |
| `fujifilm` | Fujifilm |
| `panasonic` | Lumix / 松下 |
| `om` | OM System / 奥林巴斯 |
| `leica` | Leica |
| `pentax` | Pentax |
| `ricoh` | Ricoh / GR |
| `hasselblad` | Hasselblad |
| `dji` | DJI |
| `sigma` | Sigma |
| `apple` | Apple / iPhone |
| `google` | Google / Pixel |

## 为什么仓库里是空的

这些是**商标**，随开源仓库分发不合适（也容易被投诉）。
本目录在 `.gitignore` 里，你放的文件只在本地生效。

自己用的话，从各品牌官网的 press / brand 页面下载 SVG；
或者用 [Wikimedia Commons](https://commons.wikimedia.org/) 的公开文件。

没有标志也能用 —— 程序会自动退回文字字标（Nikon / SONY / Canon / FUJIFILM …）。
