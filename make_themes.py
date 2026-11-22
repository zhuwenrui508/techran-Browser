# -*- coding: utf-8 -*-
"""生成主题包：D:\\AquaBrowser\\src\\themes\\*.json"""
import json
import os

OUT = r"D:\AquaBrowser\src\themes"
os.makedirs(OUT, exist_ok=True)

THEMES = [
    {
        "file": "aurora",
        "name": "极光青",
        "value": "linear-gradient(160deg,#8ff3d6 0%,#3ec6c0 38%,#2b8fa8 72%,#245d86 100%)",
        "representative": "#3ec6c0",
        "opacity": 82, "blur": 28,
    },
    {
        "file": "sakura",
        "name": "樱花粉",
        "value": "linear-gradient(160deg,#ffe3ef 0%,#ffb3cf 34%,#f78fb3 66%,#d96a9a 100%)",
        "representative": "#f78fb3",
        "opacity": 84, "blur": 30,
    },
    {
        "file": "midnight",
        "name": "午夜蓝",
        "value": "linear-gradient(160deg,#3a5f9e 0%,#2b4478 40%,#1d2f57 72%,#121d38 100%)",
        "representative": "#2b4478",
        "opacity": 76, "blur": 26,
    },
    {
        "file": "mint",
        "name": "薄荷绿",
        "value": "linear-gradient(160deg,#d4f5e9 0%,#9fe3cd 36%,#66c9ae 70%,#3f9e88 100%)",
        "representative": "#9fe3cd",
        "opacity": 86, "blur": 30,
    },
    {
        "file": "peach",
        "name": "蜜桃橙",
        "value": "linear-gradient(160deg,#ffe0c2 0%,#ffc09a 34%,#ff9f7a 66%,#ef7d63 100%)",
        "representative": "#ff9f7a",
        "opacity": 84, "blur": 28,
    },
    {
        "file": "galaxy",
        "name": "银河紫",
        "value": "linear-gradient(160deg,#6f5bd6 0%,#4b3a9e 38%,#332670 70%,#1e1748 100%)",
        "representative": "#4b3a9e",
        "opacity": 78, "blur": 26,
    },
    {
        "file": "citrus",
        "name": "柑橘黄",
        "value": "linear-gradient(160deg,#fff3b0 0%,#ffe066 34%,#ffc53d 68%,#f0a500 100%)",
        "representative": "#ffe066",
        "opacity": 88, "blur": 30,
    },
    {
        "file": "dusk",
        "name": "暮色",
        "value": "linear-gradient(160deg,#ffb37a 0%,#e8738f 32%,#8a5c9e 66%,#3b3566 100%)",
        "representative": "#e8738f",
        "opacity": 82, "blur": 28,
    },
    {
        "file": "steel",
        "name": "冷钢蓝",
        "value": "linear-gradient(160deg,#cfd9e6 0%,#9db0c9 36%,#6d829f 70%,#455568 100%)",
        "representative": "#9db0c9",
        "opacity": 88, "blur": 30,
    },
    {
        "file": "mono",
        "name": "极简灰",
        "value": "linear-gradient(160deg,#f7f7f9 0%,#e6e6ea 40%,#cfcfd6 72%,#adadb8 100%)",
        "representative": "#e6e6ea",
        "opacity": 90, "blur": 32,
    },
]

for t in THEMES:
    data = {
        "name": t["name"],
        "author": "微尽索",
        "type": "gradient",
        "value": t["value"],
        "representative": t["representative"],
        "opacity": t["opacity"],
        "blur": t["blur"],
    }
    p = os.path.join(OUT, t["file"] + ".json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("写入", os.path.basename(p), "-", t["name"])

# 格式说明
readme = """# 微尽索浏览器 · 主题目录

把 `.json` 主题文件放进这个文件夹，浏览器会自动识别（菜单 →「🔄 重新加载主题」立即生效）。

## 主题文件格式

```json
{
  "name": "极光青",
  "author": "你的名字",
  "type": "gradient",
  "value": "linear-gradient(160deg,#8ff3d6 0%,#3ec6c0 38%,#2b8fa8 72%,#245d86 100%)",
  "representative": "#3ec6c0",
  "opacity": 82,
  "blur": 28
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 否 | 显示名称，缺省用文件名 |
| `author` | 否 | 作者署名 |
| `type` | 是 | `gradient` 渐变 / `color` 纯色 / `image` 图片 |
| `value` | 是 | 渐变写 CSS，纯色写 `#RRGGBB`，图片写同目录下的文件名 |
| `representative` | 否 | 取色基准色，玻璃界面会跟着它变色 |
| `opacity` | 否 | 选中后自动套用的玻璃不透明度（20~100，越大越实） |
| `blur` | 否 | 选中后自动套用的毛玻璃模糊（0~60） |

## 图片主题示例

把 `wallpaper.jpg` 和下面这个 json 放在同一目录：

```json
{
  "name": "我的壁纸",
  "type": "image",
  "value": "wallpaper.jpg",
  "representative": "#5a6b7c"
}
```

## 纯色主题示例

```json
{ "name": "深海", "type": "color", "value": "#123456", "representative": "#123456" }
```
"""
with open(os.path.join(OUT, "README-主题格式.md"), "w", encoding="utf-8") as f:
    f.write(readme)
print("写入 README-主题格式.md")
print("共", len(THEMES), "个主题")
