# 品牌标志来源

仓库**不附带**任何标志文件（见 `README.md` 的说明）。这份文档只是记录“如果要用官方标，一般从哪里来”。

## 自动获取

```bash
python src/fetch_logos.py --list        # 清单
python src/fetch_logos.py --all         # Wikimedia Commons 原件
python src/fetch_logos.py --all --source jsdelivr   # 国内网络可直连（8 个品牌）
```

## 手动来源

| 品牌 | 文件（Wikimedia Commons） | 备注 |
|---|---|---|
| Nikon | `Nikon_Logo.svg` | 方形完整标（黄底 + 射线 + 字） |
| Sony | `Sony_logo.svg` | 字标 |
| Canon | `Canon_wordmark.svg` | 字标（衬线） |
| Fujifilm | `Fujifilm_logo.svg` | 字标 |
| Lumix / Panasonic | `Lumix_logo.svg` | 字标 |
| OM System | `OM-System-Logo.svg` | 方形徽章 |
| Leica | `Leica_Camera.svg` | 圆形徽章 |
| Pentax | `Pentax_Logo.svg` | 字标 |
| Ricoh | `Ricoh_logo_2012.svg` | 字标（含 tagline） |
| Hasselblad | `Hasselblad_logo.svg` | 超宽字标 |
| DJI | `DJI_Innovations_logo.svg` | 图形标 |
| Sigma | `SIGMA_CORPORATION.svg` | 字标 |
| Apple | `Apple_logo_black.svg` | 苹果图形 |
| Google | `Google_2015_logo.svg` | 字标 |

Wikimedia 的直链规则：`https://upload.wikimedia.org/wikipedia/commons/<md5首字符>/<md5前两位>/<文件名>`
（`fetch_logos.py` 就是按这个规则算地址的。）

各国官网的 press / brand 页面通常也提供矢量文件，质量更好，可以优先。

## 版权与商标

这些标志的著作权/商标权归各公司所有。仓库只提供**下载方式**，不分发文件本体。
个人作品发布一般属于合理使用范围；商业用途（接单、广告、印刷）请自行确认各品牌的商标使用规范。
