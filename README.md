# 微尽索浏览器 · AquaBrowser

> 基于 PySide6 + QtWebEngine 的 Windows 浏览器，内置 Chromium 内核，自带明亮亚克力界面与可自定义主题包。

![版本](https://img.shields.io/badge/version-3.8-blue)
![平台](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey)
![许可](https://img.shields.io/badge/license-MIT-green)

## 特性

- **真·多标签**：每个标签独立 `QWebEngineView`，切走再切回页面不重载（Scratch 游戏状态保留）
- **内置 Chromium**：随程序打包，不依赖系统是否安装 Edge
- **明亮亚克力界面**：Windows 11 原生 `DWMWA_SYSTEMBACKDROP_TYPE` 磨砂玻璃 + 圆角窗口 + 浅色标题栏
- **主题包系统**：`themes/*.json` 拖进去就能用，主题目录可自定义（C 盘 / D 盘任意位置）
- **背景驱动取色**：玻璃界面自动跟随新标签页背景色相变化
- **8 个搜索引擎**：百度 / Google / 必应 / 搜狗 / 雅虎 / Brave / DuckDuckGo / 360
- **3 种翻译引擎**：百度翻译（默认，国内直连）/ 必应 / Google
- **3 种界面语言**：简体中文 / 繁體中文 / English
- **原生右键菜单**：网页 JS 拦不住，含翻译、下载网页、查看源码
- **真插件**：请求层广告拦截、网页暗色模式（只改网页不改界面）
- **AI 助手侧栏**：可配置 OpenAI 兼容 API

## 安装

### 方式一：安装包（推荐）

下载 `微尽索浏览器-安装包-v3.8.exe`，双击运行。安装时可自选安装盘，勾选创建桌面快捷方式。

安装完成后：

- 程序目录：`<你选的盘>\AquaBrowser`
- 主题目录：`<安装目录>\themes`（10 个内置主题 + 格式说明）
- 桌面快捷方式：`微尽索浏览器`

### 方式二：源码运行

```bash
pip install PySide6
python aqua_browser_qt.py
```

## 自定义主题

在主题目录放一个 `.json` 即可，菜单 →「🔄 重新加载主题」立即生效。

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
| `name` | 否 | 显示名称 |
| `type` | 是 | `gradient` / `color` / `image` |
| `value` | 是 | 渐变 CSS / `#RRGGBB` / 同目录图片文件名 |
| `representative` | 否 | 取色基准，玻璃界面跟着它变色 |
| `opacity` | 否 | 玻璃不透明度 20~100 |
| `blur` | 否 | 毛玻璃模糊 0~60 |

详见 `themes/README-主题格式.md`。

## 目录结构

```
aqua_browser_qt.py     主程序
i18n.py                多语言词条表
themes/                主题包（10 个 json + 格式说明）
installer/             Inno Setup 安装脚本
AquaBrowserQt.spec     PyInstaller 打包配置
make_icon.py           SVG → ico/png 图标生成
make_themes.py         主题包生成
make_lnk_v38.py        创建桌面快捷方式（IShellLinkW）
```

## 自行打包

```bash
# 1) 打包程序
python -m PyInstaller AquaBrowserQt.spec --distpath dist --workpath build --noconfirm

# 2) 编译安装包（改 aqua_browser.iss 里的 SrcDir / ThemeDir 为本机路径）
"C:\Program Files\Inno Setup 6\ISCC.exe" installer\aqua_browser.iss
```

## 反馈

欢迎提 Issue。提交时请附上：

- 版本号（菜单 →「关于」可查看）
- Windows 版本
- 复现步骤
- 截图或录屏

## 许可

MIT License，详见 [LICENSE](LICENSE)。

## 致谢

- [PySide6](https://www.qt.io/qt-for-python) / Qt WebEngine
- [Inno Setup](https://jrsoftware.org/isinfo.php)
