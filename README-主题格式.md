# 微尽索浏览器 · 主题目录

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
