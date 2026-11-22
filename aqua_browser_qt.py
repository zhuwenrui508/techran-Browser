# -*- coding: utf-8 -*-
"""
微尽索浏览器 · Qt / WebEngine 版
=================================
- 真·多标签：每个标签一个独立 QWebEngineView，切换只是显示/隐藏，页面不重载
  （Scratch 游戏切走再切回来，状态保留）
- 自带 Chromium 内核：随 EXE 打包，不依赖系统是否装 Edge
- 原生右键菜单：Qt 原生 QMenu，网页 JS 拦不住
- 真插件：广告拦截（请求层真拦截）、暗色模式（真注入样式）
- AI 助手：接 OpenAI 兼容 API，可配置服务商/端点/密钥/模型
"""
import os
import sys
import json
import time
import ctypes
from ctypes import wintypes, Structure, c_int, c_uint, POINTER, byref
import urllib.request
import urllib.parse
import ssl

import i18n
from i18n import t

from PySide6.QtCore import (
    Qt, QUrl, QThread, Signal, QObject, QTimer, QSettings
)
from PySide6.QtGui import (
    QAction, QIcon, QColor, QPalette, QFont, QCursor, QDesktopServices, QKeySequence,
    QImage, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QToolBar, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QMenu, QMessageBox, QInputDialog,
    QLabel, QTextBrowser, QFrame, QComboBox, QDialog, QFormLayout, QSizePolicy,
    QSplitter, QProgressBar, QToolButton, QStackedWidget, QSlider, QListWidget,
    QListWidgetItem, QAbstractItemView, QColorDialog, QFileDialog, QTabBar,
    QGridLayout
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
    QWebEngineUrlRequestInterceptor, QWebEngineScript
)

APP_NAME = "微尽索浏览器"
VER = "v3.8"
VER_NOTE = "浅色菜单"      # 中文版代号，仅在中文界面显示
# ---- 创作者信息（发版前改这里即可，关于界面会显示）----
CREATOR_NAME = "微尽索"        # 创作者昵称
CREATOR_CHANNEL = "微尽索"     # 视频号名称
CREATOR_CHANNEL_ID = ""        # 视频号 ID（可留空）
PROJECT_URL = "https://github.com/"   # 开源仓库地址（发布后填）
# 现代无衬线字体栈：西文 Segoe UI Variable → Segoe UI，
# 中文 HarmonyOS Sans SC → 微软雅黑 UI
FONT_STACK = ('"Segoe UI Variable", "Segoe UI", "HarmonyOS Sans SC", '
              '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif')
FONT_FAMILIES = ["Segoe UI Variable", "Segoe UI", "HarmonyOS Sans SC",
                 "Microsoft YaHei UI", "Microsoft YaHei"]
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aqua_qt_settings.json")
HOME_URL = "https://www.baidu.com"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
)

AI_PRESETS = [
    {"name": "DeepSeek", "endpoint": "https://api.deepseek.com/chat/completions", "model": "deepseek-chat"},
    {"name": "通义千问", "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "model": "qwen-plus"},
    {"name": "Kimi", "endpoint": "https://api.moonshot.cn/v1/chat/completions", "model": "moonshot-v1-8k"},
    {"name": "OpenAI", "endpoint": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o-mini"},
    {"name": "本地 Ollama", "endpoint": "http://localhost:11434/v1/chat/completions", "model": "qwen2.5"},
]

# AI 网页版站点：在侧边栏里加载，让用户自己登录（无需 API 密钥）
AI_SITES = [
    {"name": "Gemini", "url": "https://gemini.google.com/", "color": "#4285F4"},
    {"name": "ChatGPT", "url": "https://chatgpt.com/", "color": "#10A37F"},
    {"name": "Grok", "url": "https://grok.com/", "color": "#1D1D1F"},
    {"name": "Claude", "url": "https://claude.ai/", "color": "#D97757"},
    {"name": "DeepSeek", "url": "https://chat.deepseek.com/", "color": "#4D6BFE"},
    {"name": "腾讯元宝", "url": "https://yuanbao.tencent.com/", "color": "#1E6FFF"},
    {"name": "腾讯混元", "url": "https://hunyuan.tencent.com/", "color": "#6C5CE7"},
    {"name": "通义千问", "url": "https://tongyi.aliyun.com/", "color": "#615CED"},
    {"name": "Kimi", "url": "https://www.kimi.com/", "color": "#19B9A6"},
    {"name": "豆包", "url": "https://www.doubao.com/chat/", "color": "#3978F6"},
    {"name": "WorkBuddy", "url": "https://www.workbuddy.cn/", "color": "#2F7BFF"},
    {"name": "Copilot", "url": "https://copilot.microsoft.com/", "color": "#0F6CBD"},
]

AD_DOMAINS = [
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "adservice.google.com", "adnxs.com", "amazon-adsystem.com", "criteo.com",
    "taboola.com", "outbrain.com", "pubmatic.com", "rubiconproject.com",
    "openx.net", "casalemedia.com", "adsrvr.org", "moatads.com",
    "scorecardresearch.com", "quantserve.com", "adcolony.com", "unityads.com",
    "applovin.com", "inmobi.com", "bannerflow.com", "adsafeprotected.com",
    "pagead2.googlesyndication.com", "hm.baidu.com", "cnzz.com", "umeng.com",
]


def app_dir():
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """用户数据目录：打包后写 exe 同级，便于持久化。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _load_settings_file(name):
    """读取 data_dir 下的 JSON（书签/下载等）"""
    try:
        p = os.path.join(data_dir(), name)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def load_settings():
    path = os.path.join(data_dir(), "aqua_qt_settings.json")
    default = {
        "theme": {"hue": 210, "opacity": 84, "blur": 28},
        # 新标签页自定义背景 + 背景驱动的玻璃取色
        "newtab": {
            "mode": "gradient",          # gradient / color / image
            "gradient": "control",       # 预设渐变 key
            "color": "#6a8ee6",          # 自定义纯色
            "image": "",                 # 本地图片路径
            "follow": True,              # 玻璃界面是否跟随背景取色/透明度
        },
        "plugins": {"adblock": True, "darkmode": False},
        "ai": {
            "preset": "DeepSeek",
            "endpoint": AI_PRESETS[0]["endpoint"],
            "api_key": "",
            "model": AI_PRESETS[0]["model"],
        },
        "home": HOME_URL,
        "search_engine": "baidu",
        "translate_engine": "baidu",   # 默认百度翻译（国内直连，不依赖梯子）
        "themes_dir": "",              # 主题目录；空=exe 同级 themes
        "language": "zh-CN",           # zh-CN / zh-TW / en
    }
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in default.items():
                if k in data:
                    if isinstance(v, dict):
                        default[k].update(data[k])
                    else:
                        default[k] = data[k]
    except Exception:
        pass
    return default


def save_settings(s):
    path = os.path.join(data_dir(), "aqua_qt_settings.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# 搜索引擎列表：(key, 名称, 搜索URL模板 {q})
SEARCH_ENGINES = [
    ("baidu", "百度", "https://www.baidu.com/s?wd={q}"),
    ("google", "Google", "https://www.google.com/search?q={q}"),
    ("bing", "必应 Bing", "https://www.bing.com/search?q={q}"),
    ("sogou", "搜狗", "https://www.sogou.com/web?query={q}"),
    ("yahoo", "雅虎 Yahoo", "https://search.yahoo.com/search?p={q}"),
    ("brave", "Brave", "https://search.brave.com/search?q={q}"),
    ("duckduckgo", "DuckDuckGo", "https://duckduckgo.com/?q={q}"),
    ("360", "360 搜索", "https://www.so.com/s?q={q}"),
]


def search_url(text, engine_key="baidu"):
    """按选定搜索引擎生成搜索 URL。"""
    tpl = "https://www.baidu.com/s?wd={q}"
    for k, name, _tpl in SEARCH_ENGINES:
        if k == engine_key:
            tpl = _tpl
            break
    return tpl.replace("{q}", urllib.parse.quote(text or ""))


def norm_url(text, engine_key="baidu"):
    text = (text or "").strip()
    if not text:
        return ""
    low = text.lower()
    if low.startswith(("http://", "https://", "file://", "about:", "data:")):
        return text
    if low.startswith("view-source:"):
        return text
    if "." in text and " " not in text:
        return "https://" + text
    return search_url(text, engine_key)


# 翻译引擎：(key, 名称, 整页翻译模板 {u}, 文本翻译模板 {t})
# 默认百度：国内可直连，不用梯子；Google 留作可选项
TRANSLATORS = [
    ("baidu", "百度翻译",
     "https://fanyi.baidu.com/transpage?query={u}&source=url&ie=utf8&from=auto&to=zh&render=1",
     "https://fanyi.baidu.com/#auto/zh/{t}"),
    ("bing", "必应翻译",
     "https://www.translatetheweb.com/?from=&to=zh-CHS&a={u}",
     "https://www.bing.com/translator?ref=TThis&from=auto&to=zh-Hans&text={t}"),
    ("google", "Google 翻译（需梯子）",
     "https://translate.google.com/translate?sl=auto&tl=zh-CN&u={u}",
     "https://translate.google.com/?sl=auto&tl=zh-CN&text={t}"),
]


def translator_name(key):
    for k, name, _p, _t in TRANSLATORS:
        if k == key:
            return name
    return TRANSLATORS[0][1]


def translate_url(kind, value, engine_key="baidu"):
    """kind='page' 传网页 URL，kind='text' 传待译文字。"""
    row = TRANSLATORS[0]
    for k, name, pt, tt in TRANSLATORS:
        if k == engine_key:
            row = (k, name, pt, tt)
            break
    tpl = row[2] if kind == "page" else row[3]
    return tpl.replace("{%s}" % ("u" if kind == "page" else "t"),
                       urllib.parse.quote(value or "", safe=""))


# ============================================================
# Windows DWM 亚克力毛玻璃（旧版蓝色毛玻璃效果的核心）
# ============================================================
class _ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_uint),
        ("AnimationId", c_int),
    ]


class _WINDOW_COMPOSITION_ATTRIBUTE(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", POINTER(_ACCENT_POLICY)),
        ("DataSize", c_int),
    ]


class _MARGINS(Structure):
    _fields_ = [("cxLeftWidth", c_int), ("cxRightWidth", c_int),
                ("cyTopHeight", c_int), ("cyBottomHeight", c_int)]


def apply_win11_backdrop(hwnd, kind=3, light=True, hue=210):
    """Windows 11 22H2+ 原生亚克力（DWMWA_SYSTEMBACKDROP_TYPE）。

    比旧版 ACCENT_POLICY 更明亮细腻，接近系统原生的磨砂质感：
      kind: 2=Mica, 3=Acrylic(磨砂玻璃), 4=Tabbed
    同时把标题栏/边框改成随主题色相的近白色（否则会跟随系统强调色变蓝），
    并开启圆角窗口、把边框延伸到客户区让亚克力铺满整窗。
    """
    try:
        dwm = ctypes.windll.dwmapi
        h = wintypes.HWND(int(hwnd))
        v = c_int(int(kind))
        # 38 = DWMWA_SYSTEMBACKDROP_TYPE；失败说明系统不支持（Win10/早期 Win11）
        if dwm.DwmSetWindowAttribute(h, 38, byref(v), ctypes.sizeof(v)) != 0:
            return False
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE：0=浅色（明亮）
        dm = c_int(0 if light else 1)
        dwm.DwmSetWindowAttribute(h, 20, byref(dm), ctypes.sizeof(dm))
        # 33 = DWMWA_WINDOW_CORNER_PREFERENCE：2=圆角
        cr = c_int(2)
        dwm.DwmSetWindowAttribute(h, 33, byref(cr), ctypes.sizeof(cr))
        # 标题栏/边框改成近白（带一点主题色），避免被系统强调色染成蓝/紫
        t = QColor.fromHsv(int(hue) % 360, 16, 250)
        caption = c_int((t.red()) | (t.green() << 8) | (t.blue() << 16))  # COLORREF 0x00BBGGRR
        dwm.DwmSetWindowAttribute(h, 35, byref(caption), ctypes.sizeof(caption))  # CAPTION_COLOR
        txt = c_int(0x1E1C1C)  # 标题文字：深灰
        dwm.DwmSetWindowAttribute(h, 36, byref(txt), ctypes.sizeof(txt))          # TEXT_COLOR
        border = c_int(0xD8D2CE)  # 边框：浅灰（COLORREF 下即 rgb(206,210,216)）
        dwm.DwmSetWindowAttribute(h, 34, byref(border), ctypes.sizeof(border))    # BORDER_COLOR
        # 把窗口边框扩展到整个客户区，亚克力才会铺满而不是只出现在标题栏
        m = _MARGINS(-1, -1, -1, -1)
        dwm.DwmExtendFrameIntoClientArea(h, byref(m))
        return True
    except Exception:
        return False


def apply_acrylic(hwnd, hue, opacity, blur):
    """给窗口启用亚克力毛玻璃：Win11 走原生 Acrylic，Win10 回退旧 API。"""
    if apply_win11_backdrop(hwnd, kind=3, light=True, hue=hue):
        return True
    try:
        accent = _ACCENT_POLICY()
        accent.AccentState = 4          # ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.AccentFlags = 2
        # 高亮亚克力：近白低饱和 + 高明度，中等不透明度以透出模糊桌面（明亮而非灰暗）
        rgb = QColor.fromHsv(int(hue) % 360, 18, 252)
        alpha = max(1, min(255, int(185 * (float(opacity) / 100.0))))
        accent.GradientColor = (alpha << 24) | (rgb.blue() << 16) | (rgb.green() << 8) | rgb.red()
        accent.AnimationId = 0
        data = _WINDOW_COMPOSITION_ATTRIBUTE()
        data.Attribute = 19
        data.Data = ctypes.cast(byref(accent), POINTER(_ACCENT_POLICY))
        data.DataSize = ctypes.sizeof(_ACCENT_POLICY)
        user32 = ctypes.windll.user32
        user32.SetWindowCompositionAttribute.argtypes = [wintypes.HWND, POINTER(_WINDOW_COMPOSITION_ATTRIBUTE)]
        user32.SetWindowCompositionAttribute(wintypes.HWND(int(hwnd)), byref(data))
        return True
    except Exception:
        return False


# 旧版同款 7 个主题色（色相），用于图形化色卡
THEME_SWATCHES = [
    ("经典蓝", 210), ("青绿", 170), ("翠绿", 130), ("橙黄", 35),
    ("珊瑚红", 8), ("品红", 320), ("紫罗兰", 270),
]


# ============================================================
# 现代明亮配色：明亮、半透明、圆角、柔和阴影
# 所有颜色由主题色相 hue 派生，色卡切换后整体协调变化
# ============================================================
def aqua_palette(hue):
    """返回一套明亮风格 CSS 颜色字典（字符串），由 hue 派生强调色。"""
    h = int(hue) % 360
    accent = QColor.fromHsv(h, 205, 245)       # 系统蓝这类高明度强调色
    accent_deep = QColor.fromHsv(h, 225, 205)  # 按下/选中态
    acc = "#%02x%02x%02x" % (accent.red(), accent.green(), accent.blue())
    acc_deep = "#%02x%02x%02x" % (accent_deep.red(), accent_deep.green(), accent_deep.blue())
    return {
        "accent": acc,
        "accent_deep": acc_deep,
        "acc_rgb": "%d,%d,%d" % (accent.red(), accent.green(), accent.blue()),
        "text": "#1c1c1e",          # 主文字（深色，配浅底）
        "text2": "#6e6e73",         # 次要文字
        # 明亮磨砂玻璃层：盖在 DWM 亚克力之上，既透出模糊桌面又保持高亮
        "glass": "rgba(255,255,255,0.46)",   # 工具栏/面板
        "card": "rgba(118,118,128,0.14)",    # 地址栏等输入：略深的玻璃胶囊（不是死白）
        "card_hover": "rgba(118,118,128,0.20)",
        # 弹出菜单是独立顶层窗口，背后没有玻璃底 → 必须近乎不透明的浅色，
        # 否则半透明色叠在黑底上会变成"黑菜单"（深色字完全看不见）
        "menu_bg": "rgba(252,252,254,0.98)",
        "tab_bg": "rgba(255,255,255,0.16)",  # 未选中标签
        "tab_sel": "rgba(255,255,255,0.86)", # 选中标签
        "line": "rgba(60,60,67,0.10)",        # 分隔线
        "shadow": "rgba(0,0,0,0.08)",
    }


# 全局样式表：应用于整个应用（QMenu 等弹层也受益）
def aqua_global_qss(p):
    return (
        "* {font-family:%s;}"
        "QToolTip{background:rgba(28,28,30,.92);color:#fff;border:none;"
        "padding:5px 9px;border-radius:7px;font-size:12px;}"
        "QMenu{background:%s;color:%s;border:1px solid %s;border-radius:12px;"
        "padding:6px 3px;}"
        "QMenu::item{padding:8px 26px 8px 14px;border-radius:7px;font-size:13px;"
        "background:transparent;}"
        "QMenu::item:selected{background:%s;color:#fff;}"
        "QMenu::item:disabled{color:%s;}"
        "QMenu::separator{height:1px;background:%s;margin:5px 8px;}"
        "QScrollBar:vertical{background:transparent;width:9px;margin:0;}"
        "QScrollBar::handle:vertical{background:rgba(142,142,147,.5);"
        "border-radius:4px;min-height:24px;}"
        "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        "QScrollBar:horizontal{background:transparent;height:9px;}"
        "QScrollBar::handle:horizontal{background:rgba(142,142,147,.5);"
        "border-radius:4px;min-width:24px;}"
    ) % (FONT_STACK, p["menu_bg"], p["text"], p["line"], p["accent"],
         p["text2"], p["line"])

# 新标签页：控制中心风格（蓝紫渐变 + 毛玻璃分组卡片 + 圆形图标 + 滑块）
NEWTAB_HTML = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{min-height:100%;font-family:"Segoe UI Variable","Segoe UI","HarmonyOS Sans SC","Microsoft YaHei UI","Microsoft YaHei",sans-serif;}
body{__BG_STYLE__;
     background-attachment:fixed;padding:34px 40px 48px;display:flex;flex-direction:column;align-items:center;}
.wrap{width:100%;max-width:900px;}
.hdr{display:flex;align-items:center;justify-content:space-between;color:#fff;margin-bottom:22px;padding:0 4px;}
.hdr .t{font-size:22px;font-weight:600;letter-spacing:.5px;text-shadow:0 2px 12px rgba(60,40,120,.25);}
.hdr .badge{font-size:12px;background:rgba(255,255,255,.28);border:1px solid rgba(255,255,255,.4);
            padding:6px 14px;border-radius:20px;backdrop-filter:blur(10px);}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}
.card{background:rgba(255,255,255,.30);border:1px solid rgba(255,255,255,.45);
      border-radius:24px;padding:18px 20px;backdrop-filter:blur(24px) saturate(160%);
      -webkit-backdrop-filter:blur(24px) saturate(160%);
      box-shadow:0 10px 30px rgba(60,60,120,.16),inset 0 1px 0 rgba(255,255,255,.5);}
.card.wide{grid-column:1 / -1;}
.card h3{font-size:15px;font-weight:700;color:#2b2b3a;margin-bottom:14px;letter-spacing:.3px;}
.row{display:flex;align-items:center;gap:13px;padding:9px 0;}
.row .ic{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;
         font-size:19px;font-weight:600;color:#fff;flex:none;box-shadow:inset 0 -6px 12px rgba(0,0,0,.12),0 3px 9px rgba(0,0,0,.12);}
.row .tx{flex:1;min-width:0;}
.row .tx b{display:block;font-size:14px;color:#1d1d1f;font-weight:600;}
.row .tx small{display:block;font-size:11.5px;color:rgba(0,0,0,.5);margin-top:2px;}
.row .chev{color:rgba(0,0,0,.32);font-size:19px;font-weight:300;}
.row[data-u]{cursor:pointer;border-radius:12px;transition:background .15s;}
.row[data-u]:hover{background:rgba(255,255,255,.3);}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.tile{background:rgba(255,255,255,.26);border:1px solid rgba(255,255,255,.42);border-radius:20px;
      padding:16px 8px;text-align:center;cursor:pointer;backdrop-filter:blur(18px);
      box-shadow:0 6px 18px rgba(60,60,120,.12);transition:transform .15s;}
.tile:hover{transform:translateY(-3px);}
.tile .ic{width:48px;height:48px;margin:0 auto 9px;border-radius:14px;display:flex;align-items:center;
          justify-content:center;font-size:20px;color:#fff;box-shadow:inset 0 -6px 12px rgba(0,0,0,.12);}
.tile b{font-size:12px;color:#1d1d1f;font-weight:600;}
.search{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.55);
        border:1px solid rgba(255,255,255,.6);border-radius:18px;padding:7px 8px 7px 16px;
        box-shadow:inset 0 1px 3px rgba(0,0,0,.05);}
.search input{flex:1;border:none;outline:none;background:transparent;font-size:14px;color:#1d1d1f;}
.search button{border:none;background:linear-gradient(135deg,#4a9bff,#2f6bff);color:#fff;font-size:13px;
        font-weight:600;padding:9px 20px;border-radius:13px;cursor:pointer;box-shadow:0 3px 10px rgba(47,107,255,.35);}
.search button:active{transform:scale(.96);}
.slider-row{display:flex;align-items:center;gap:12px;padding:8px 0;}
.slider-row .lab{font-size:13px;color:#2b2b3a;font-weight:600;width:64px;flex:none;}
.slider-row .track{flex:1;height:7px;border-radius:5px;background:rgba(0,0,0,.12);position:relative;overflow:visible;}
.slider-row .fill{position:absolute;left:0;top:0;height:100%;border-radius:5px;background:rgba(255,255,255,.95);}
.slider-row .knob{position:absolute;top:50%;width:20px;height:20px;border-radius:50%;background:#fff;
        transform:translate(-50%,-50%);box-shadow:0 2px 7px rgba(0,0,0,.22);}
/* 页面内背景自定义浮层 */
.bgfab{position:fixed;right:26px;bottom:26px;width:52px;height:52px;border-radius:26px;
       background:rgba(255,255,255,.36);border:1px solid rgba(255,255,255,.6);backdrop-filter:blur(18px);
       box-shadow:0 8px 24px rgba(60,60,120,.22);display:flex;align-items:center;justify-content:center;
       font-size:23px;cursor:pointer;z-index:20;transition:transform .15s;}
.bgfab:hover{transform:scale(1.08);}
.bgpanel{position:fixed;right:26px;bottom:90px;width:300px;padding:18px;z-index:21;display:none;
         background:rgba(255,255,255,.45);border:1px solid rgba(255,255,255,.7);border-radius:22px;
         backdrop-filter:blur(26px) saturate(160%);box-shadow:0 16px 44px rgba(40,40,90,.24);}
.bgpanel.show{display:block;}
.bgpanel h4{font-size:14px;color:#1d1d1f;margin-bottom:12px;font-weight:700;}
.swatches{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:14px;}
.swatches .sw{width:38px;height:38px;border-radius:19px;cursor:pointer;border:3px solid transparent;
              box-shadow:0 2px 8px rgba(0,0,0,.12);}
.swatches .sw.on{border-color:#1d1d1f;}
.bgrow{display:flex;align-items:center;gap:10px;margin:10px 0;font-size:12px;color:#2b2b3a;}
.bgrow input[type=color]{width:44px;height:32px;border:none;border-radius:8px;cursor:pointer;background:transparent;}
.bgrow input[type=range]{flex:1;}
.bgrow .tg{margin-left:auto;padding:5px 10px;border-radius:9px;background:#e5e5ea;color:#1d1d1f;
           cursor:pointer;font-size:11px;font-weight:600;border:none;}
.bgrow .tg.on{background:#34c759;color:#fff;}
.bgclose{position:absolute;right:12px;top:10px;font-size:18px;color:rgba(0,0,0,.4);cursor:pointer;}
</style></head><body>
<div class="wrap">
  <div class="hdr"><div class="t">微尽索浏览器</div><div class="badge">__NT_BADGE__</div></div>

  <div class="card wide" style="margin-bottom:16px;">
    <div class="search"><input id="q" placeholder="__NT_SEARCH_PH__"><button id="go">__NT_SEARCH_BTN__</button></div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>__NT_QUICK__</h3>
      <div class="row" data-u="https://www.baidu.com"><div class="ic" style="background:linear-gradient(135deg,#5b9bff,#2f6bff)">百</div><div class="tx"><b>百度</b><small>搜索 · 全球中文信息</small></div><span class="chev">›</span></div>
      <div class="row" data-u="https://www.bilibili.com"><div class="ic" style="background:linear-gradient(135deg,#ff9ec4,#fb7299)">B</div><div class="tx"><b>哔哩哔哩</b><small>视频 · 弹幕社区</small></div><span class="chev">›</span></div>
      <div class="row" data-u="https://www.zhihu.com"><div class="ic" style="background:linear-gradient(135deg,#5aa8ff,#0066ff)">知</div><div class="tx"><b>知乎</b><small>问答 · 知识分享</small></div><span class="chev">›</span></div>
      <div class="row" data-u="https://www.scratch-cw.top"><div class="ic" style="background:linear-gradient(135deg,#ffb44d,#ff8c1a)">S</div><div class="tx"><b>Scratch</b><small>创作 · 编程乐园</small></div><span class="chev">›</span></div>
    </div>

    <div class="card">
      <h3>__NT_TOOLS__</h3>
      <div class="tiles">
        <div class="tile" data-u="https://chat.deepseek.com/"><div class="ic" style="background:linear-gradient(135deg,#7a8cff,#4a5bff)">✦</div><b>AI 助手</b></div>
        <div class="tile" data-u="https://github.com"><div class="ic" style="background:linear-gradient(135deg,#5a5f6a,#24292e)">GH</div><b>GitHub</b></div>
        <div class="tile" data-u="https://www.bilibili.com"><div class="ic" style="background:linear-gradient(135deg,#ff9ec4,#fb7299)">▶</div><b>视频</b></div>
        <div class="tile" data-u="https://mail.qq.com"><div class="ic" style="background:linear-gradient(135deg,#5bc0ff,#1685ff)">✉</div><b>邮箱</b></div>
        <div class="tile" data-u="https://www.zhihu.com"><div class="ic" style="background:linear-gradient(135deg,#7ed0c0,#1abc9c)">知</div><b>阅读</b></div>
        <div class="tile" data-u="https://www.baidu.com"><div class="ic" style="background:linear-gradient(135deg,#a0a6b0,#6b7280)">⋮</div><b>更多</b></div>
      </div>
    </div>

    <div class="card wide">
      <h3>__NT_APPEARANCE__</h3>
      <div class="slider-row"><div class="lab">__NT_OPACITY__</div><div class="track live" data-k="opacity" data-min="20" data-max="100"><div class="fill" style="width:__OPACITY__%"></div><div class="knob" style="left:__OPACITY__%"></div></div></div>
      <div class="slider-row"><div class="lab">__NT_BLUR__</div><div class="track live" data-k="blur" data-min="0" data-max="60"><div class="fill" style="width:__BLURPCT__%"></div><div class="knob" style="left:__BLURPCT__%"></div></div></div>
    </div>
  </div>
</div>

<div class="bgfab" id="bgfab" title="__NT_CUSTOM_BG__">🎨</div>
<div class="bgpanel" id="bgpanel">
  <span class="bgclose" id="bgclose">×</span>
  <h4>__NT_CUSTOM_BG__</h4>
  <div class="swatches" id="swatches">__BG_SWATCHES__</div>
  <div class="bgrow"><span>__NT_SOLID__</span><input type="color" id="bgcolor" value="#6a8ee6">
    <button class="tg" id="applycolor">__NT_APPLY__</button></div>
  <div class="bgrow"><span>__NT_OPACITY__</span><input type="range" id="bgopacity" min="20" max="100" value="94"></div>
  <div class="bgrow"><span>__NT_BLUR__</span><input type="range" id="bgblur" min="0" max="60" value="28"></div>
  <div class="bgrow"><span>__NT_FOLLOW__</span><button class="tg on" id="bgfollow">__NT_ON__</button></div>
</div>

<script>
function nav(v){
  if(!v) return;
  if(!/^https?:\/\//i.test(v)){
    if(/^[\w-]+(\.[\w-]+)+([\/?#].*)?$/.test(v)) v='https://'+v;
    else v='__SEARCH_TPL__'.replace('{q}',encodeURIComponent(v));
  }
  location.href=v;
}
document.getElementById('go').onclick=function(){nav(document.getElementById('q').value.trim());};
document.getElementById('q').addEventListener('keydown',function(e){if(e.keyCode===13)nav(this.value.trim());});
document.querySelectorAll('[data-u]').forEach(function(s){
  s.onclick=function(){nav(s.getAttribute('data-u'));};
});
/* ---- 页面内背景自定义：通过 console 通知浏览器 ---- */
function aqSend(cmd){ console.log('__AQ_BG__|'+cmd); }
var fab=document.getElementById('bgfab'), panel=document.getElementById('bgpanel');
fab.onclick=function(){ panel.classList.toggle('show'); };
document.getElementById('bgclose').onclick=function(){ panel.classList.remove('show'); };
document.querySelectorAll('#swatches .sw').forEach(function(sw){
  sw.onclick=function(){
    document.querySelectorAll('#swatches .sw').forEach(function(x){x.classList.remove('on');});
    sw.classList.add('on');
    aqSend('gradient='+sw.getAttribute('data-k'));
  };
});
document.getElementById('applycolor').onclick=function(){
  aqSend('color='+document.getElementById('bgcolor').value.replace('#',''));
};
document.getElementById('bgopacity').oninput=function(){ aqSend('opacity='+this.value); };
document.getElementById('bgblur').oninput=function(){ aqSend('blur='+this.value); };
/* 「外观」卡片里的滑块：可直接拖动，实时改玻璃浓度/模糊 */
document.querySelectorAll('.track.live').forEach(function(el){
  var k=el.getAttribute('data-k'), mn=+el.getAttribute('data-min'), mx=+el.getAttribute('data-max');
  function setAt(clientX){
    var r=el.getBoundingClientRect();
    var p=Math.max(0,Math.min(1,(clientX-r.left)/Math.max(1,r.width)));
    var v=Math.round(mn+p*(mx-mn));
    el.querySelector('.fill').style.width=(p*100)+'%';
    el.querySelector('.knob').style.left=(p*100)+'%';
    aqSend(k+'='+v);
  }
  el.addEventListener('pointerdown',function(e){
    try{el.setPointerCapture(e.pointerId);}catch(_){}
    el.classList.add('drag'); setAt(e.clientX);
  });
  el.addEventListener('pointermove',function(e){ if(el.classList.contains('drag')) setAt(e.clientX); });
  el.addEventListener('pointerup',function(){ el.classList.remove('drag'); });
  el.addEventListener('pointercancel',function(){ el.classList.remove('drag'); });
});
var followBtn=document.getElementById('bgfollow');
followBtn.onclick=function(){
  var on=!followBtn.classList.contains('on');
  followBtn.classList.toggle('on',on); followBtn.textContent=on?'开':'关';
  aqSend('follow='+(on?'1':'0'));
};
</script></body></html>"""


# ============================================================
# 新标签页自定义背景 + 背景驱动的玻璃取色（透明反应）
# ============================================================
import base64 as _b64

# 预设渐变：(key, 名称, CSS 渐变, 代表色用于取色)
NEWTAB_GRADIENTS = [
    ("control", "控制中心蓝紫", "linear-gradient(160deg,#7ec8f5 0%,#5aa9ed 28%,#6a8ee6 55%,#8a7de6 80%,#a86fd8 100%)", "#6a8ee6"),
    ("ocean", "深海蓝", "linear-gradient(160deg,#43c6ac 0%,#3a9fd0 50%,#2b6cb0 100%)", "#3a9fd0"),
    ("sunset", "日落橙粉", "linear-gradient(160deg,#ff9a9e 0%,#f6ad55 50%,#fecfef 100%)", "#f6ad55"),
    ("forest", "森林绿", "linear-gradient(160deg,#a8e063 0%,#56ab2f 50%,#2e8b57 100%)", "#56ab2f"),
    ("violet", "星云紫", "linear-gradient(160deg,#c471ed 0%,#8a5cf6 50%,#4a3f9f 100%)", "#8a5cf6"),
    ("slate", "石墨灰", "linear-gradient(160deg,#bdc3c7 0%,#8896a6 50%,#4b5b6b 100%)", "#8896a6"),
]


def _hex_to_rgb(h):
    h = (h or "").lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (106, 142, 230)


# ============================================================
# 主题文件系统
# ============================================================
# 主题文件格式（放在「主题目录」下的 *.json）：
# {
#   "name": "极光",                        // 显示名称
#   "author": "微尽索",                    // 作者（可选）
#   "type": "gradient",                    // gradient / color / image
#   "value": "linear-gradient(160deg,...)",// 渐变CSS / #RRGGBB / 同目录图片文件名
#   "representative": "#5aa9ed",           // 取色基准（玻璃跟随用）
#   "opacity": 84,                         // 可选：选中后自动套用的玻璃不透明度
#   "blur": 28                             // 可选：毛玻璃模糊
# }
THEME_TYPES = ("gradient", "color", "image")


def themes_dir(settings=None):
    """主题目录：settings 指定 > exe 同级 themes > 程序目录 themes。"""
    cands = []
    if settings:
        d = str(settings.get("themes_dir") or "").strip()
        if d:
            cands.append(d)
    cands.append(os.path.join(data_dir(), "themes"))
    cands.append(os.path.join(app_dir(), "themes"))
    for d in cands:
        if d and os.path.isdir(d):
            return d
    d = os.path.join(data_dir(), "themes")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def load_theme_files(settings=None):
    """扫描主题目录下的 *.json，返回主题列表（坏文件静默跳过）。"""
    out = []
    d = themes_dir(settings)
    try:
        files = sorted(os.listdir(d))
    except Exception:
        return out
    for fn in files:
        if not fn.lower().endswith(".json"):
            continue
        path = os.path.join(d, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
            ttype = str(data.get("type") or "gradient").strip().lower()
            if ttype not in THEME_TYPES:
                continue
            val = str(data.get("value") or "").strip()
            if not val:
                continue
            if ttype == "image" and not os.path.isabs(val):
                val = os.path.join(d, val)
            out.append({
                "key": "file:" + os.path.splitext(fn)[0],
                "name": str(data.get("name") or os.path.splitext(fn)[0]),
                "author": str(data.get("author") or ""),
                "type": ttype,
                "value": val,
                "rep": str(data.get("representative") or "#6a8ee6"),
                "opacity": data.get("opacity"),
                "blur": data.get("blur"),
                "path": path,
            })
        except Exception:
            continue
    return out


def theme_by_key(settings, key):
    for t in load_theme_files(settings):
        if t["key"] == key:
            return t
    return None


def bg_spec(settings):
    """把设置解析成统一背景描述 (type, value, rep)。"""
    nt = settings.get("newtab", {})
    mode = nt.get("mode", "gradient")
    if mode == "theme":
        t = theme_by_key(settings, nt.get("theme", ""))
        if t:
            return t["type"], t["value"], t["rep"]
        mode = "gradient"          # 主题文件被删了 → 回退默认渐变
    if mode == "color" and nt.get("color"):
        return "color", nt["color"], nt["color"]
    if mode == "image" and nt.get("image"):
        return "image", nt["image"], ""
    key = nt.get("gradient", "control")
    for k, name, css, rep in NEWTAB_GRADIENTS:
        if k == key:
            return "gradient", css, rep
    return "gradient", NEWTAB_GRADIENTS[0][2], NEWTAB_GRADIENTS[0][3]


def bg_choices(settings):
    """给 UI 用的背景清单：内置渐变在前，主题文件在后。"""
    out = [(k, name, "gradient", css, rep) for k, name, css, rep in NEWTAB_GRADIENTS]
    for t in load_theme_files(settings):
        if t["type"] in ("gradient", "color"):
            sw = t["value"]
        else:  # 图片主题用代表色做一个示意色块
            sw = "linear-gradient(135deg,%s,%s)" % (t["rep"], t["rep"])
        out.append((t["key"], t["name"], t["type"], sw, t["rep"]))
    return out


def current_bg_key(settings):
    """当前选中的背景 key（用于色卡高亮）。"""
    nt = settings.get("newtab", {})
    mode = nt.get("mode", "gradient")
    if mode == "theme":
        return nt.get("theme", "")
    if mode in ("color", "image"):
        return ""
    return nt.get("gradient", "control")


def newtab_bg_css(settings):
    """返回新标签页 body 的 background 样式；图片用 base64 data URI。"""
    kind, val, _rep = bg_spec(settings)
    if kind == "image" and val:
        try:
            ext = os.path.splitext(val)[1].lstrip(".").lower() or "png"
            if ext == "jpg":
                ext = "jpeg"
            with open(val, "rb") as f:
                data = _b64.b64encode(f.read()).decode("ascii")
            return "background:url(data:image/%s;base64,%s) center/cover no-repeat" % (ext, data)
        except Exception:
            pass
    if kind == "color" and val:
        return "background:%s" % val
    return "background:%s" % (val or NEWTAB_GRADIENTS[0][2])


def bg_representative_rgb(settings):
    """取背景代表色 RGB，供毛玻璃取色。"""
    kind, val, rep = bg_spec(settings)
    if kind == "color" and val:
        return _hex_to_rgb(val)
    if kind == "image" and val:
        try:
            img = QImage(val)
            if not img.isNull():
                img = img.convertToFormat(QImage.Format_RGB32)
                img = img.scaled(1, 1)  # 缩到 1x1 取平均色
                c = QColor(img.pixel(0, 0))
                return (c.red(), c.green(), c.blue())
        except Exception:
            pass
    return _hex_to_rgb(rep or NEWTAB_GRADIENTS[0][3])


def rgb_to_hue(r, g, b):
    return int(QColor(int(r), int(g), int(b)).hue() % 360)


def effective_hue(settings):
    """跟随背景时返回背景代表色相，否则返回用户手动色相。"""
    nt = settings.get("newtab", {})
    if nt.get("follow", True):
        r, g, b = bg_representative_rgb(settings)
        return rgb_to_hue(r, g, b)
    return int(settings.get("theme", {}).get("hue", 210))


def palette_for(settings):
    """按当前有效色相生成界面配色（含背景驱动的透明反应）。"""
    return aqua_palette(effective_hue(settings))


def build_newtab_html(settings):
    """按当前背景 + 搜索引擎设置生成新标签页 HTML。"""
    html = NEWTAB_HTML.replace("__BG_STYLE__", newtab_bg_css(settings))
    eng = settings.get("search_engine", "baidu")
    tpl = "https://www.baidu.com/s?wd={q}"
    for k, name, _tpl in SEARCH_ENGINES:
        if k == eng:
            tpl = _tpl
            break
    html = html.replace("__SEARCH_TPL__", tpl)
    # 生成背景色卡（内置渐变 + 主题文件），标记当前选中
    nt = settings.get("newtab", {})
    cur = current_bg_key(settings)
    sw = "".join(
        '<div class="sw%s" data-k="%s" title="%s" style="background:%s"></div>'
        % (" on" if k == cur else "", k, name, css)
        for k, name, kind, css, rep in bg_choices(settings)
    )
    html = html.replace("__BG_SWATCHES__", sw)
    # 初始化控件值
    html = html.replace('value="#6a8ee6">', 'value="%s">' % nt.get("color", "#6a8ee6"))
    html = html.replace('id="bgopacity" min="20" max="100" value="94"',
                        'id="bgopacity" min="20" max="100" value="%d"' % settings["theme"].get("opacity", 94))
    html = html.replace('id="bgblur" min="0" max="60" value="28"',
                        'id="bgblur" min="0" max="60" value="%d"' % settings["theme"].get("blur", 28))
    # 「外观」卡片滑块按当前设置初始化位置
    op = int(settings["theme"].get("opacity", 94))
    bl = int(settings["theme"].get("blur", 28))
    # 多语言文案
    _nt_map = {
        "__NT_BADGE__": t("nt.badge"),
        "__NT_SEARCH_PH__": t("nt.search_ph"),
        "__NT_SEARCH_BTN__": t("nt.search_btn"),
        "__NT_QUICK__": t("nt.quick"),
        "__NT_TOOLS__": t("nt.tools"),
        "__NT_APPEARANCE__": t("nt.appearance"),
        "__NT_OPACITY__": t("nt.opacity"),
        "__NT_BLUR__": t("nt.blur"),
        "__NT_CUSTOM_BG__": t("nt.custom_bg"),
        "__NT_SOLID__": t("nt.solid"),
        "__NT_APPLY__": t("nt.apply"),
        "__NT_FOLLOW__": t("nt.follow"),
        "__NT_ON__": t("nt.follow_on"),
    }
    for _k, _v in _nt_map.items():
        html = html.replace(_k, _v)
    html = html.replace("__OPACITY__", str(max(20, min(100, op))))
    html = html.replace("__BLURPCT__", str(int(max(0, min(60, bl)) / 60 * 100)))
    fol = nt.get("follow", True)
    html = html.replace('<button class="tg on" id="bgfollow">开</button>',
                        '<button class="tg %s" id="bgfollow">%s</button>' % ("on" if fol else "", "开" if fol else "关"))
    return html


# ============================================================
# 广告拦截：请求层真拦截
# ============================================================
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, enabled=True, parent=None):
        super().__init__(parent)
        self.enabled = enabled
        self.blocked = 0

    def set_enabled(self, on):
        self.enabled = bool(on)

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl().toString().lower()
        for d in AD_DOMAINS:
            if d in url:
                info.block(True)
                self.blocked += 1
                return


# ============================================================
# AI 请求线程（不阻塞界面）
# ============================================================
class AIWorker(QThread):
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, endpoint, api_key, model, messages, parent=None):
        super().__init__(parent)
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.messages = messages

    def run(self):
        try:
            payload = json.dumps({
                "model": self.model,
                "messages": self.messages,
                "temperature": 0.7,
                "stream": False,
            }).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = "Bearer " + self.api_key
            req = urllib.request.Request(self.endpoint, data=payload, headers=headers)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                raw = resp.read().decode("utf-8", "ignore")
            data = json.loads(raw)
            content = ""
            choices = data.get("choices") or []
            if choices:
                content = (choices[0].get("message") or {}).get("content", "")
            if not content:
                content = data.get("message") or raw[:500]
            self.done.emit(content)
        except Exception as e:
            self.failed.emit(str(e))


# ============================================================
# 单个网页标签
# ============================================================
class AqPage(QWebEnginePage):
    """拦截新标签页里的 console 指令，让网页能直接改浏览器背景/透明设置。"""
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window

    def javaScriptConsoleMessage(self, level, message, line, source):
        try:
            if message.startswith("__AQ_BG__|"):
                payload = message.split("|", 1)[1]
                nt = self.window.settings.setdefault("newtab", {})
                # payload: mode=xxx&value=xxx&follow=0/1
                for part in payload.split("&"):
                    if "=" not in part:
                        continue
                    k, v = part.split("=", 1)
                    if k == "gradient":
                        if v.startswith("file:"):
                            # 主题文件：切到 theme 模式，并套用它声明的玻璃参数
                            nt["mode"] = "theme"
                            nt["theme"] = v
                            t = theme_by_key(self.window.settings, v)
                            if t:
                                if isinstance(t.get("opacity"), (int, float)):
                                    self.window.settings["theme"]["opacity"] = int(t["opacity"])
                                if isinstance(t.get("blur"), (int, float)):
                                    self.window.settings["theme"]["blur"] = int(t["blur"])
                        else:
                            nt["mode"] = "gradient"
                            nt["gradient"] = v
                    elif k == "color":
                        nt["mode"] = "color"; nt["color"] = "#" + v.lstrip("#")
                    elif k == "follow":
                        nt["follow"] = (v == "1")
                    elif k == "opacity":
                        self.window.settings["theme"]["opacity"] = int(v)
                    elif k == "blur":
                        self.window.settings["theme"]["blur"] = int(v)
                save_settings(self.window.settings)
                self.window._apply_theme()
                # 透明度/模糊度只重绘玻璃，不重建 HTML（避免滑块失焦）；背景变更才重建
                if "gradient" not in payload and "color" not in payload and "follow" not in payload:
                    pass
                else:
                    self.window.refresh_newtabs()
        except Exception:
            pass
        # 不打印普通日志，避免刷屏


class BrowserTab(QWebEngineView):
    def __init__(self, window, url=""):
        super().__init__()
        self.window = window
        self.setPage(AqPage(window, self))
        self._title = "新标签页"
        self.titleChanged.connect(self._on_title)
        self.urlChanged.connect(self._on_url)
        self.loadFinished.connect(self._on_loaded)
        self._apply_settings()
        if url:
            self.setUrl(QUrl(url))

    def _apply_settings(self):
        s = self.page().settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        try:
            s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        except Exception:
            pass
        self.page().profile().setHttpUserAgent(DEFAULT_UA)

    def _on_title(self, t):
        # 新标签页阶段忽略网页标题（about:blank 之类），保持"新标签页"
        if getattr(self, "_is_newtab", False):
            return
        self._title = t or self._title
        self.window.on_tab_title_changed(self)

    def _on_url(self, u):
        # 新标签页里点了站点/搜索后，转正为普通网页标签
        if getattr(self, "_is_newtab", False):
            try:
                if u.toString().lower().startswith(("http://", "https://")):
                    self._is_newtab = False
                    self.window.on_tab_title_changed(self)
            except Exception:
                pass
        self.window.on_tab_url_changed(self)

    def _on_loaded(self, ok):
        self.window.on_tab_loaded(self, ok)
        if self.window.settings["plugins"]["darkmode"] and not getattr(self, "_is_newtab", False):
            self.apply_dark_mode()

    def apply_dark_mode(self):
        js = r"""
        (function(){
          if(document.getElementById('__aq_dark')) return;
          var s=document.createElement('style');
          s.id='__aq_dark';
          s.textContent='html,body{filter:invert(.88) hue-rotate(180deg)!important;background:#111!important;}'+
                        'img,video,iframe{filter:invert(1) hue-rotate(180deg)!important;}';
          (document.head||document.documentElement).appendChild(s);
        })();
        """
        self.page().runJavaScript(js)

    def clear_dark_mode(self):
        self.page().runJavaScript(
            "var e=document.getElementById('__aq_dark');if(e)e.remove();"
        )

    def createWindow(self, typ):
        # target=_blank 一律在新标签打开，不弹新窗口
        view = BrowserTab(self.window, "")
        self.window.add_tab_with_view(view, "新标签页")
        return view.page()

    def contextMenuEvent(self, event):
        # 兼容不同 PySide6 版本：
        # 老版 event 是 QWebEngineContextMenuEvent，需用 event.request() 取请求；
        # 新版 event 本身就是 QWebEngineContextMenuRequest，直接就是请求对象。
        req = None
        try:
            req = event.request()
        except Exception:
            req = event
        menu = QMenu(self)
        try:
            link = req.linkUrl().toString() if req else ""
            text = req.selectedText() if req else ""
            media = req.mediaUrl().toString() if req else ""
        except Exception:
            link, text, media = "", "", ""

        if link:
            a = menu.addAction("在新标签页打开链接")
            a.triggered.connect(lambda: self.window.add_tab(link))
            a = menu.addAction("复制链接地址")
            a.triggered.connect(lambda: QApplication.clipboard().setText(link))
            menu.addSeparator()

        if text:
            a = menu.addAction('搜索 "%s"' % text[:18])
            a.triggered.connect(
                lambda: self.window.add_tab(search_url(text, self.window.settings.get("search_engine", "baidu")))
            )
            # AI 子菜单：选中文字 → 选 AI → 复制文字并在侧边栏打开该 AI 网页版
            ai_menu = menu.addMenu("用 AI 处理选中文字")
            for s in AI_SITES:
                a = ai_menu.addAction(s["name"])
                a.triggered.connect(lambda checked, n=s["name"], t=text: self.window.ask_ai_web(n, t))
            ai_menu.addSeparator()
            a = ai_menu.addAction("API 对话（需密钥）")
            a.triggered.connect(lambda: self.window.ask_ai("请解释下面这段内容：\n\n" + text))
            a = menu.addAction("复制")
            a.triggered.connect(lambda: QApplication.clipboard().setText(text))
            menu.addSeparator()

        if media:
            a = menu.addAction("复制图片/媒体地址")
            a.triggered.connect(lambda: QApplication.clipboard().setText(media))
            menu.addSeparator()

        a = menu.addAction("后退")
        a.triggered.connect(self.back)
        a.setEnabled(self.page().history().canGoBack())
        a = menu.addAction("前进")
        a.triggered.connect(self.forward)
        a.setEnabled(self.page().history().canGoForward())
        a = menu.addAction("刷新")
        a.triggered.connect(self.reload)
        menu.addSeparator()
        # 翻译：选中文字翻选中，没选中翻整页（引擎可在菜单里切，默认百度）
        _tr = translator_name(self.window.settings.get("translate_engine", "baidu"))
        if text:
            a = menu.addAction('翻译选中文字："%s"' % text[:16])
            a.triggered.connect(lambda: self.window.translate_page(text))
        a = menu.addAction("翻译此网页（%s）" % _tr)
        a.triggered.connect(lambda: self.window.translate_page())
        menu.addSeparator()
        a = menu.addAction("下载此网页 HTML")
        a.triggered.connect(self.window.download_page_html)
        a = menu.addAction("打开下载文件夹")
        a.triggered.connect(self.window.open_download_folder)
        menu.addSeparator()
        a = menu.addAction("查看网页源码")
        a.triggered.connect(
            lambda: self.window.add_tab("view-source:" + self.url().toString())
        )
        # 弹窗位置：优先事件里的鼠标位置，取不到就用当前光标，保证一定能弹出
        try:
            pos = event.globalPos()
        except Exception:
            pos = QCursor.pos()
        menu.exec(pos)


# ============================================================
# AI 助手面板
# ============================================================
class AIPanel(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.messages = []
        self.worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        # 顶部：站点下拉 + 刷新 + API对话切换 + 设置 + 关闭
        head = QHBoxLayout()
        p = palette_for(self.window.settings)
        self.site_combo = QComboBox()
        self.site_combo.addItems([s["name"] for s in AI_SITES])
        self.site_combo.setStyleSheet(
            "QComboBox{background:%s;color:%s;border:1px solid %s;"
            "border-radius:9px;padding:6px 9px;font-size:12px;}"
            "QComboBox::drop-down{border:none;}"
            "QComboBox QAbstractItemView{background:#ffffff;color:%s;border:1px solid %s;}"
            % (p["card"], p["text"], p["line"], p["text"], p["line"])
        )
        self.site_combo.currentTextChanged.connect(self.on_site_changed)
        head.addWidget(self.site_combo, 1)

        _tb = ("QToolButton{color:%s;font-size:15px;background:transparent;border:none;"
               "border-radius:7px;padding:3px 6px;}"
               "QToolButton:hover{background:rgba(120,120,128,.14);}" % p["text"])

        refresh = QToolButton()
        refresh.setText("↻")
        refresh.setToolTip("刷新当前 AI 页面")
        refresh.setStyleSheet(_tb)
        refresh.clicked.connect(self.refresh_site)
        head.addWidget(refresh)

        self.mode_btn = QToolButton()
        self.mode_btn.setText("💬")
        self.mode_btn.setToolTip("切换到 API 对话模式（需密钥）")
        self.mode_btn.setStyleSheet(_tb)
        self.mode_btn.clicked.connect(self.toggle_mode)
        head.addWidget(self.mode_btn)

        cfg = QToolButton()
        cfg.setText("⚙")
        cfg.setToolTip("AI 设置")
        cfg.setStyleSheet(_tb)
        cfg.clicked.connect(self.window.open_ai_settings)
        head.addWidget(cfg)

        close = QToolButton()
        close.setText("✕")
        close.setToolTip("收起侧边栏")
        close.setStyleSheet(_tb)
        close.clicked.connect(self.window.toggle_ai)
        head.addWidget(close)
        lay.addLayout(head)

        # 两种内容：网页版视图 + API 对话
        self.stack = QStackedWidget()

        self.ai_web = QWebEngineView()
        self.ai_web.setUrl(QUrl(AI_SITES[0]["url"]))  # 默认 Gemini
        self.stack.addWidget(self.ai_web)  # index 0

        api_widget = QWidget()
        api_lay = QVBoxLayout(api_widget)
        api_lay.setContentsMargins(0, 4, 0, 0)
        api_lay.setSpacing(6)
        self.provider = QLabel("")
        self.provider.setStyleSheet("color:%s;font-size:11px;" % p["text2"])
        api_lay.addWidget(self.provider)
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(True)
        self.chat.setStyleSheet(
            "QTextBrowser{background:%s;color:%s;"
            "border:1px solid %s;border-radius:11px;font-size:13px;padding:8px;}"
            % (p["card"], p["text"], p["line"])
        )
        api_lay.addWidget(self.chat, 1)
        row = QHBoxLayout()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("问点什么…（Enter 发送）")
        self.edit.setStyleSheet(
            "QLineEdit{background:%s;color:%s;border:1px solid %s;"
            "border-radius:11px;padding:7px 11px;font-size:13px;}"
            % (p["card"], p["text"], p["line"])
        )
        self.edit.returnPressed.connect(self.send)
        row.addWidget(self.edit, 1)
        self.send_btn = QPushButton("发送")
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setStyleSheet(
            "QPushButton{background:%s;color:#fff;border:none;border-radius:11px;"
            "padding:7px 16px;font-size:13px;font-weight:600;}"
            "QPushButton:pressed{background:%s;}" % (p["accent"], p["accent_deep"])
        )
        self.send_btn.clicked.connect(self.send)
        row.addWidget(self.send_btn)
        api_lay.addLayout(row)
        self.stack.addWidget(api_widget)  # index 1

        lay.addWidget(self.stack, 1)
        self.api_mode = False
        self.refresh_provider()

    def on_site_changed(self, name):
        if self.api_mode:
            self.toggle_mode()  # 选站点时自动回到网页版
        for s in AI_SITES:
            if s["name"] == name:
                self.ai_web.setUrl(QUrl(s["url"]))
                break

    def refresh_site(self):
        if not self.api_mode:
            self.ai_web.reload()

    def toggle_mode(self):
        self.api_mode = not self.api_mode
        self.stack.setCurrentIndex(1 if self.api_mode else 0)
        self.mode_btn.setText("🌐" if self.api_mode else "💬")
        self.mode_btn.setToolTip("切换到 AI 网页版" if self.api_mode else "切换到 API 对话模式（需密钥）")

    def open_site(self, name):
        """右键菜单调用：打开指定 AI 网页版并切到网页模式"""
        if self.api_mode:
            self.toggle_mode()
        idx = self.site_combo.findText(name)
        if idx >= 0:
            self.site_combo.setCurrentIndex(idx)

    def refresh_provider(self):
        ai = self.window.settings["ai"]
        self.provider.setText("当前：%s · %s" % (ai.get("preset", "自定义"), ai.get("model", "")))
        if not ai.get("api_key") and "localhost" not in ai.get("endpoint", ""):
            self.provider.setText(self.provider.text() + "（未配置密钥，点 ⚙ 设置；或用上方网页版免密钥）")

    def append(self, who, text):
        color = "#7fd4ff" if who == "你" else "#fff"
        name = "你" if who == "你" else "AI"
        self.chat.append('<div style="color:%s;font-weight:600;margin-top:8px;">%s</div>' % (color, name))
        safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self.chat.append('<div style="color:#e8e8e8;line-height:1.6;">%s</div>' % safe)
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def send(self, preset_text=None):
        text = preset_text if preset_text is not None else self.edit.text().strip()
        if not text:
            return
        if not preset_text:
            self.edit.clear()
        self.append("你", text)
        self.messages.append({"role": "user", "content": text})
        self.messages = self.messages[-12:]

        ai = self.window.settings["ai"]
        self.send_btn.setEnabled(False)
        self.append("AI", "思考中…")

        self.worker = AIWorker(
            ai.get("endpoint", ""), ai.get("api_key", ""), ai.get("model", ""),
            list(self.messages), self
        )
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_done(self, content):
        # 去掉"思考中…"最后一条
        self.chat.setPlainText("")
        for m in self.messages:
            self.append("你" if m["role"] == "user" else "AI", m["content"])
        self.messages.append({"role": "assistant", "content": content})
        self.messages = self.messages[-12:]
        self.append("AI", content)
        self.send_btn.setEnabled(True)

    def on_failed(self, err):
        self.chat.setPlainText("")
        for m in self.messages:
            self.append("你" if m["role"] == "user" else "AI", m["content"])
        self.append("AI", "[调用失败] " + err)
        self.send_btn.setEnabled(True)


# ============================================================
# 功能面板：插件 / 外观 / 书签 / 历史 / 下载（旧界面那套功能补回来）
# ============================================================
class FeaturePanel(QDialog):
    PLUGINS = [
        ("adblock", "广告拦截", "在请求层真实拦截广告域名", "⛔"),
        ("darkmode", "网页暗色", "只让网页变暗，界面仍保持明亮", "◐"),
        ("ai", "AI 助手侧栏", "右侧小窗打开 12 个 AI 网页版", "✦"),
    ]
    STORE = [
        ("adblock", "广告拦截器", "真实拦截广告请求", "⛔", "#E74C3C", "隐私"),
        ("darkmode", "网页暗色", "网站内容变暗，界面不变", "◐", "#2C3E50", "外观"),
        ("ai", "AI 助手", "12 大 AI 侧栏", "✦", "#2F7BFF", "工具"),
        ("screenshot", "网页截图", "整屏截图存下载目录", "▣", "#3498DB", "工具"),
        ("translate", "网页翻译", "选中文字/整页翻译", "译", "#1ABC9B", "工具"),
    ]

    def __init__(self, window, tab="plugins"):
        super().__init__(window)
        self.window = window
        p = palette_for(window.settings)
        self.setWindowTitle(APP_NAME + " · " + ("功能中心" if i18n.get_lang().startswith("zh") else "Control Center"))
        self.resize(720, 520)
        self.setStyleSheet(
            "QDialog{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #7ec8f5,stop:.35 #6a8ee6,stop:.7 #8a7de6,stop:1 #a86fd8);color:%s;}"
            "QLabel{color:%s;font-size:13px;background:transparent;}"
            "QPushButton{background:%s;color:#fff;border:none;border-radius:9px;padding:8px 16px;}"
            "QPushButton:pressed{background:%s;}"
            % (p["text"], p["text"], p["accent"], p["accent_deep"])
        )
        lay = QHBoxLayout(self)
        nav = QListWidget()
        nav.setFixedWidth(150)
        nav.setStyleSheet(
            "QListWidget{background:rgba(255,255,255,.5);color:%s;border:none;border-radius:11px;}"
            "QListWidget::item{padding:11px 14px;border-radius:8px;}"
            "QListWidget::item:selected{background:%s;color:#fff;}"
            % (p["text"], p["accent"])
        )
        for key in ("plugins", "store", "theme", "bookmarks", "history", "downloads"):
            nav.addItem(QListWidgetItem(t("nav." + key)))
        lay.addWidget(nav)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self._build_plugins(); self._build_store(); self._build_theme()
        self._build_bookmarks(); self._build_history(); self._build_downloads()
        nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        idx = ["plugins", "store", "theme", "bookmarks", "history", "downloads"].index(tab) if tab in ["plugins", "store", "theme", "bookmarks", "history", "downloads"] else 0
        nav.setCurrentRow(idx)
        # 统一禁用所有 QLabel 的文本交互，避免截图/焦点时出现深灰选中背景块
        for lab in self.findChildren(QLabel):
            lab.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def _page(self):
        w = QWidget()
        w.setStyleSheet(
            "QWidget{background:rgba(255,255,255,.42);border:1px solid rgba(255,255,255,.6);"
            "border-radius:22px;}"
        )
        lay = QVBoxLayout(w); lay.setContentsMargins(20, 18, 20, 18)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stack.addWidget(w); return w, lay

    def _build_plugins(self):
        p = palette_for(self.window.settings)
        w, lay = self._page()
        lay.addWidget(QLabel("已安装插件（开关即时生效）"))
        self.plugin_toggles = {}
        for key, name, desc, icon in self.PLUGINS:
            cell = QFrame()
            cell.setStyleSheet(
                "QFrame{background:rgba(255,255,255,.5);border:1px solid rgba(255,255,255,.65);"
                "border-radius:16px;}"
            )
            row = QHBoxLayout(cell)
            row.setContentsMargins(12, 9, 12, 9)
            name_lab = QLabel(icon + "  " + name)
            name_lab.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            name_lab.setStyleSheet("color:%s;font-size:14px;font-weight:600;background:transparent;" % p["text"])
            desc_lab = QLabel(desc)
            desc_lab.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            desc_lab.setStyleSheet("color:%s;font-size:11px;background:transparent;" % p["text2"])
            txt = QVBoxLayout(); txt.setSpacing(1)
            txt.addWidget(name_lab); txt.addWidget(desc_lab)
            row.addLayout(txt, 1)
            t = QToolButton(); t.setText("开" if self._plugin_on(key) else "关")
            t.setCheckable(True); t.setChecked(self._plugin_on(key))
            t.setCursor(QCursor(Qt.PointingHandCursor))
            t.setStyleSheet(
                "QToolButton{padding:6px 16px;border-radius:11px;background:#e5e5ea;color:%s;"
                "min-width:44px;font-weight:600;}"
                "QToolButton:checked{background:#34c759;color:#fff;}" % p["text"]
            )
            t.toggled.connect(lambda on, k=key: self._toggle_plugin(k, on))
            self.plugin_toggles[key] = t
            row.addWidget(t)
            lay.addWidget(cell)

    def _plugin_on(self, key):
        s = self.window.settings["plugins"]
        if key == "ai":
            return self.window.ai.isVisible()
        return bool(s.get(key, False))

    def _toggle_plugin(self, key, on):
        if key == "ai":
            if on and not self.window.ai.isVisible():
                self.window.toggle_ai()
            elif not on and self.window.ai.isVisible():
                self.window.toggle_ai()
            return
        self.window.settings["plugins"][key] = on
        save_settings(self.window.settings)
        if key == "adblock":
            self.window.blocker.set_enabled(on)
        elif key == "darkmode":
            for i in range(self.window.tabs.count()):
                v = self.window.tabs.widget(i)
                if isinstance(v, BrowserTab):
                    v.apply_dark_mode() if on else v.clear_dark_mode()

    def _build_store(self):
        w, lay = self._page()
        lay.addWidget(QLabel("插件商店（点击安装/卸载，真实生效）"))
        for key, name, desc, icon, color, cat in self.STORE:
            row = QHBoxLayout()
            row.addWidget(QLabel(icon + "  " + name + "  —  " + desc + "  [" + cat + "]"))
            row.addStretch()
            installed = key in ("adblock", "darkmode", "ai") or key in self.window.settings["plugins"]
            b = QPushButton("卸载" if installed else "安装")
            b.setStyleSheet("QPushButton{background:%s;color:#fff;border:none;border-radius:8px;padding:6px 14px;}" % color)
            row.addWidget(b); lay.addLayout(row)

    def _build_theme(self):
        p = palette_for(self.window.settings)
        w, lay = self._page()
        # 默认搜索引擎
        eng_row = QHBoxLayout(); eng_row.addWidget(QLabel(t("theme.default_search")))
        eng = QComboBox()
        eng.addItems([name for k, name, t in SEARCH_ENGINES])
        ce = self.window.settings.get("search_engine", "baidu")
        for k, nm, _tpl in SEARCH_ENGINES:
            if k == ce:
                eng.setCurrentText(nm); break
        def on_eng():
            for k, nm, _tpl in SEARCH_ENGINES:
                if nm == eng.currentText():
                    self.window.settings["search_engine"] = k
                    save_settings(self.window.settings)
                    self.window.refresh_newtabs()
                    break
        eng.currentTextChanged.connect(on_eng)
        eng_row.addWidget(eng, 1); lay.addLayout(eng_row)
        # 默认翻译引擎（默认百度，国内直连）
        tr_row = QHBoxLayout(); tr_row.addWidget(QLabel(t("theme.default_translate")))
        trc = QComboBox()
        trc.addItems([name for k, name, pt, tt in TRANSLATORS])
        ctr = self.window.settings.get("translate_engine", "baidu")
        trc.setCurrentText(translator_name(ctr))

        def on_tr():
            for k, nm, pt, tt in TRANSLATORS:
                if nm == trc.currentText():
                    self.window.settings["translate_engine"] = k
                    save_settings(self.window.settings)
                    break
        trc.currentTextChanged.connect(on_tr)
        tr_row.addWidget(trc, 1); lay.addLayout(tr_row)
        lay.addWidget(QLabel(t("theme.ui_color")))
        row = QHBoxLayout()
        cur = int(self.window.settings["theme"].get("hue", 210))
        for name, hue in THEME_SWATCHES:
            b = QToolButton(); b.setToolTip(name); b.setFixedSize(40, 40)
            col = QColor.fromHsv(hue, 170, 105)
            b.setStyleSheet("QToolButton{border:3px solid %s;border-radius:20px;background:%s;}"
                            % (p["accent"] if hue == cur else "transparent", col.name()))
            b.clicked.connect(lambda _, h=hue: (self.window.settings["theme"].__setitem__("hue", h),
                                                 save_settings(self.window.settings), self.window._apply_theme()))
            row.addWidget(b)
        lay.addLayout(row)
        for label, key, rng in [(t("theme.opacity"), "opacity", (20, 100)), (t("theme.blur"), "blur", (0, 60))]:
            r = QHBoxLayout(); r.addWidget(QLabel(label))
            sl = QSlider(Qt.Orientation.Horizontal); sl.setRange(*rng)
            sl.setValue(int(self.window.settings["theme"].get(key, rng[1])))
            sl.valueChanged.connect(lambda v, k=key: (self.window.settings["theme"].__setitem__(k, v),
                                                      save_settings(self.window.settings), self.window._apply_theme()))
            r.addWidget(sl, 1); lay.addLayout(r)

        # ---------- 标签页背景：内置渐变 + 主题文件 ----------
        lay.addWidget(QLabel(t("theme.newtab_bg")))
        nt = self.window.settings.setdefault("newtab", {})
        choices = bg_choices(self.window.settings)
        cur_key = current_bg_key(self.window.settings)
        rep_map = {k: rp for k, n, kd, cs, rp in choices}
        grid = QGridLayout()
        grid.setSpacing(6)
        sw_btns = []
        for i, (key, name, kind, css, rep) in enumerate(choices):
            b = QToolButton()
            b.setToolTip(name + ("（主题文件）" if key.startswith("file:") else ""))
            b.setFixedSize(36, 36)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet("QToolButton{border:3px solid %s;border-radius:18px;background:%s;}"
                            % (p["accent"] if key == cur_key else "transparent", rep))
            sw_btns.append((b, key))
            grid.addWidget(b, i // 6, i % 6)
        lay.addLayout(grid)

        def pick(key):
            if key.startswith("file:"):
                nt["mode"] = "theme"
                nt["theme"] = key
                t = theme_by_key(self.window.settings, key)
                if t:
                    if isinstance(t.get("opacity"), (int, float)):
                        self.window.settings["theme"]["opacity"] = int(t["opacity"])
                    if isinstance(t.get("blur"), (int, float)):
                        self.window.settings["theme"]["blur"] = int(t["blur"])
            else:
                nt["mode"] = "gradient"
                nt["gradient"] = key
            save_settings(self.window.settings)
            self.window._apply_theme()
            self.window.refresh_newtabs()
            for b2, k2 in sw_btns:
                b2.setStyleSheet("QToolButton{border:3px solid %s;border-radius:18px;background:%s;}"
                                 % (p["accent"] if k2 == key else "transparent",
                                    rep_map.get(k2, "#6a8ee6")))

        for b, key in sw_btns:
            b.clicked.connect(lambda _=False, k=key: pick(k))

        th_row = QHBoxLayout()
        for txt, slot in ((t("theme.open_folder"), self.window.open_themes_folder),
                          (t("theme.choose_dir"), self.window.choose_themes_dir),
                          (t("theme.reload"), self.window.reload_themes)):
            tb = QPushButton(txt)
            tb.setCursor(QCursor(Qt.PointingHandCursor))
            tb.setStyleSheet("QPushButton{background:%s;color:#fff;border:none;border-radius:10px;"
                             "padding:7px 10px;font-size:12px;}" % p["accent"])
            tb.clicked.connect(slot)
            th_row.addWidget(tb)
        lay.addLayout(th_row)
        hint = QLabel(t("theme.dir_hint", dir=themes_dir(self.window.settings),
                        n=len(load_theme_files(self.window.settings))))
        hint.setStyleSheet("color:%s;font-size:11px;" % p["text2"])
        hint.setWordWrap(True)
        hint.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        lay.addWidget(hint)

    def _build_bookmarks(self):
        w, lay = self._page()
        lst = QListWidget(); lst.setStyleSheet("QListWidget{background:rgba(255,255,255,.55);color:#1c1c1e;border:1px solid rgba(60,60,67,.10);border-radius:12px;padding:6px;}")
        data = _load_settings_file("aqua_bookmarks.json")
        for b in data if isinstance(data, list) else []:
            lst.addItem(b.get("name", "") + "  —  " + b.get("url", ""))
        if lst.count() == 0:
            lst.addItem("（暂无书签，浏览网页时点工具栏 ☆ 添加）")
        lay.addWidget(lst)

    def _build_history(self):
        w, lay = self._page()
        lst = QListWidget(); lst.setStyleSheet("QListWidget{background:rgba(255,255,255,.55);color:#1c1c1e;border:1px solid rgba(60,60,67,.10);border-radius:12px;padding:6px;}")
        hist = getattr(self.window, "history", [])
        for h in hist[-50:][::-1]:
            lst.addItem(str(h.get("title", h.get("url", ""))) + "  —  " + str(h.get("url", "")))
        if lst.count() == 0:
            lst.addItem("（暂无历史记录）")
        lay.addWidget(lst)

    def _build_downloads(self):
        w, lay = self._page()
        lst = QListWidget(); lst.setStyleSheet("QListWidget{background:rgba(255,255,255,.55);color:#1c1c1e;border:1px solid rgba(60,60,67,.10);border-radius:12px;padding:6px;}")
        data = _load_settings_file("aqua_downloads.json")
        for d in data if isinstance(data, list) else []:
            lst.addItem(d.get("name", "") + "  —  " + d.get("path", ""))
        if lst.count() == 0:
            lst.addItem("（暂无下载记录）")
        lay.addWidget(lst)


# ============================================================
# 主窗口
# ============================================================
class BrowserWindow(QMainWindow):
    def __init__(self, start_url=""):
        super().__init__()
        self.settings = load_settings()
        self.history = _load_settings_file("aqua_history.json")
        if not isinstance(self.history, list):
            self.history = []
        self.setWindowTitle(APP_NAME + " " + VER)
        self.resize(1280, 820)
        # 应用图标（任务栏/标题栏/Alt-Tab 都用它）
        for _ic in ("app_icon.ico", "app_icon.png"):
            _p = os.path.join(app_dir(), _ic)
            if os.path.exists(_p):
                self.setWindowIcon(QIcon(_p))
                break
        # 关键：窗口背景透明，DWM 亚克力毛玻璃才能透出来（否则被不透明背景盖住）
        # AQ_OPAQUE=1 可关闭（排查 WebEngine 合成问题时用）
        if os.environ.get("AQ_OPAQUE") != "1":
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.blocker = AdBlocker(self.settings["plugins"]["adblock"], self)
        prof = QWebEngineProfile.defaultProfile()
        prof.setUrlRequestInterceptor(self.blocker)

        self._build_ui()
        self._apply_theme()

        if start_url:
            self.add_tab(start_url)
        else:
            self.add_tab("")

    # ---------- UI ----------
    def _build_ui(self):
        # 顶层 central：垂直布局 = 工具栏 + 标签栏 + 内容，位置完全由布局控制
        root = QWidget()
        root.setObjectName("centralwidget")
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        self.setCentralWidget(root)

        bar = QWidget()
        bar.setObjectName("navbar")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(6, 5, 6, 5)
        bar_lay.setSpacing(5)

        p = palette_for(self.settings)

        def btn(text, tip, slot, w=34):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            b.setFixedWidth(w)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet(
                "QToolButton{color:%s;font-size:17px;background:transparent;"
                "border-radius:9px;padding:4px 0;}"
                "QToolButton:hover{background:rgba(120,120,128,.14);}"
                "QToolButton:pressed{background:rgba(120,120,128,.24);}"
                % p["text"]
            )
            bar_lay.addWidget(b)
            return b

        self.back_btn = btn("←", "后退", self.go_back)
        self.fwd_btn = btn("→", "前进", self.go_forward)
        self.reload_btn = btn("↻", "刷新", self.reload_page)
        self.home_btn = btn("⌂", "主页", self.go_home)

        self.url = QLineEdit()
        self.url.setPlaceholderText("搜索或输入网址")
        self.url.returnPressed.connect(self.navigate)
        self.url.setStyleSheet(
            "QLineEdit{background:%s;color:%s;border:1px solid %s;"
            "border-radius:13px;padding:7px 15px;font-size:13px;}"
            "QLineEdit:focus{border:1px solid %s;}"
            % (p["card"], p["text"], p["line"], p["accent"])
        )
        self.url.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url.setMinimumWidth(300)
        bar_lay.addWidget(self.url, 1)

        # 注意：clicked 会传 checked(bool)，绝不能直接连到带默认参数的 add_tab
        btn("+", "新标签页 (Ctrl+T)", lambda: self.add_tab(""))
        self.menu_btn = btn("☰", "菜单", self.show_menu)
        self.ai_toggle = btn("✦", "AI 助手（选择模型）", self.show_ai_menu)
        root_lay.addWidget(bar)

        # 标签 + AI 面板
        self.ai = AIPanel(self)
        self.tabs = QTabWidget()
        # 用自定义可见的 × 按钮（setTabButton），不依赖内置 close-button
        self.tabs.setTabsClosable(False)
        self.tabs.currentChanged.connect(self.on_current_changed)
        self.tabs.tabBar().setFixedHeight(36)
        self._style_tabs()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.ai)
        self.splitter.setSizes([1000, 300])
        self.ai.hide()
        root_lay.addWidget(self.splitter, 1)

        self.status = QLabel("")
        self.status.setStyleSheet("color:%s;font-size:11px;padding:3px 12px;background:transparent;"
                                  % p["text2"])
        root_lay.addWidget(self.status)

    def _style_tabs(self):
        """标签栏样式：强调色跟随当前背景取色。"""
        p = palette_for(self.settings)
        self.tabs.setStyleSheet(
            "QTabWidget::pane{border:none;background:transparent;top:0px;}"
            "QTabWidget::tab-bar{left:8px;}"
            "QTabBar{background:transparent;}"
            "QTabBar::tab{background:%s;color:%s;"
            "padding:8px 18px;border-radius:11px 11px 0 0;margin-right:4px;"
            "border:1px solid %s;border-bottom:none;min-width:90px;}"
            "QTabBar::tab:selected{background:%s;color:%s;font-weight:600;"
            "border-bottom:2px solid %s;}"
            "QTabBar::tab:hover:!selected{background:rgba(255,255,255,.6);}"
            % (p["tab_bg"], p["text2"], p["line"], p["tab_sel"], p["text"], p["accent"])
        )

    def _apply_theme(self):
        t = self.settings["theme"]
        hue = effective_hue(self.settings)          # 跟随背景时自动取色
        opacity = int(t.get("opacity", 94))
        blur = int(t.get("blur", 28))
        a = max(0, min(1, opacity / 100.0))
        p = aqua_palette(hue)
        # 亚克力毛玻璃（Win11 原生 Acrylic，透出桌面并模糊）
        try:
            self.show()
            apply_acrylic(int(self.winId()), hue, opacity, blur)
        except Exception:
            pass
        # 玻璃层不透明度由滑块驱动：越小越透（看得清桌面模糊），越大越亮越实
        nav_a = int(max(38, min(217, (0.15 + a * 0.70) * 255)))
        nav_a2 = int(max(26, min(235, nav_a - 22)))
        # 工具栏顶亮底略暗的竖向渐变，做出磨砂玻璃的高光感
        self.setStyleSheet(
            "QMainWindow{background:transparent;}"
            "QWidget#centralwidget{background:transparent;}"
            "QWidget#navbar{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 rgba(255,255,255,%d), stop:1 rgba(255,255,255,%d));"
            "border-bottom:1px solid %s;}"
            "QTabWidget::pane{border:none;background:transparent;}"
            % (nav_a, nav_a2, p["line"])
            + aqua_global_qss(p)
        )
        pal = self.palette()
        # 基色取主题色相的低饱和高明度色（白中透一点点背景色）→ 界面随背景变色
        tint = QColor.fromHsv(int(hue) % 360, 24, 254)
        pal.setColor(QPalette.Window,
                     QColor(tint.red(), tint.green(), tint.blue(), nav_a))
        pal.setColor(QPalette.WindowText, QColor(p["text"]))
        pal.setColor(QPalette.Text, QColor(p["text"]))
        pal.setColor(QPalette.ButtonText, QColor(p["text"]))
        self.setPalette(pal)
        self._style_tabs()

    # ---------- 标签管理 ----------
    def current_tab(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, BrowserTab) else None

    def add_tab(self, url=""):
        # 防御：clicked 等信号会把 checked(bool) 传进来，绝不能当 url 处理
        if not isinstance(url, str):
            url = ""
        view = BrowserTab(self, url)
        if not url:
            view.setHtml(build_newtab_html(self.settings), QUrl("about:blank"))
            view._is_newtab = True
        else:
            view._is_newtab = False
        try:
            title = QUrl(url).host() or url[:20] or "新标签页"
        except Exception:
            title = url[:20] if isinstance(url, str) else "新标签页"
        if not url:
            title = "新标签页"
        self.add_tab_with_view(view, title)

    def add_tab_with_view(self, view, title):
        idx = self.tabs.addTab(view, title[:24])
        # 自定义可见的关闭按钮（QTabWidget 自带 close-button 在自定义 QSS 下易隐藏）
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setToolTip("关闭标签页")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            "QToolButton{color:#6e6e73;font-size:16px;font-weight:600;background:transparent;"
            "border:none;border-radius:6px;padding:0px;}"
            "QToolButton:hover{background:rgba(0,0,0,.14);color:#c0392b;}"
        )
        close_btn.clicked.connect(lambda _=False, i=idx: self.close_tab_by_button(close_btn))
        self.tabs.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, close_btn)
        self.tabs.setCurrentIndex(idx)
        self.sync_url()

    def close_tab_by_button(self, btn):
        """通过标签上的 × 按钮关闭：反查按钮所在标签索引。"""
        bar = self.tabs.tabBar()
        for i in range(self.tabs.count()):
            if bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is btn:
                self.close_tab(i)
                return

    def refresh_newtabs(self):
        """背景设置变化后，刷新所有处于新标签页状态的视图。"""
        html = build_newtab_html(self.settings)
        for i in range(self.tabs.count()):
            v = self.tabs.widget(i)
            if isinstance(v, BrowserTab) and getattr(v, "_is_newtab", False):
                v.setHtml(html, QUrl("about:blank"))

    def close_tab(self, idx):
        w = self.tabs.widget(idx)
        if isinstance(w, BrowserTab):
            w.page().setParent(None)
            w.deleteLater()
        self.tabs.removeTab(idx)
        if self.tabs.count() == 0:
            self.add_tab("")

    def on_tab_title_changed(self, view):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            title = (view._title or "网页")[:24]
            self.tabs.setTabText(idx, title)

    def on_tab_url_changed(self, view):
        if view is self.current_tab():
            self.sync_url()

    def on_tab_loaded(self, view, ok):
        if view is self.current_tab():
            self.sync_url()
            self.status.setText("加载完成" if ok else "部分内容未能加载")
        # 记录历史（http(s) 网页）
        try:
            url = view.url().toString()
            title = view._title or url
            if url.lower().startswith(("http://", "https://")):
                self.history = [h for h in self.history if h.get("url") != url]
                self.history.insert(0, {"url": url, "title": title, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
                self.history = self.history[:200]
                try:
                    with open(os.path.join(data_dir(), "aqua_history.json"), "w", encoding="utf-8") as f:
                        json.dump(self.history, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        except Exception:
            pass

    def on_current_changed(self, idx):
        self.sync_url()

    def sync_url(self):
        v = self.current_tab()
        if v:
            self.url.setText("" if getattr(v, "_is_newtab", False) else v.url().toString())
            self.back_btn.setEnabled(v.page().history().canGoBack())
            self.fwd_btn.setEnabled(v.page().history().canGoForward())

    # ---------- 导航 ----------
    def navigate(self):
        v = self.current_tab()
        if not v:
            self.add_tab("")
            v = self.current_tab()
        v.setUrl(QUrl(norm_url(self.url.text(), self.settings.get("search_engine", "baidu"))))

    def go_back(self):
        v = self.current_tab()
        if v:
            v.back()

    def go_forward(self):
        v = self.current_tab()
        if v:
            v.forward()

    def reload_page(self):
        v = self.current_tab()
        if v:
            v.reload()

    def go_home(self):
        v = self.current_tab()
        if v:
            v.setUrl(QUrl(self.settings.get("home", HOME_URL)))

    def show_ai_menu(self):
        """工具栏 ✦ 按钮：弹出 AI 站点列表，点选后在右侧窄栏加载网页版"""
        m = QMenu(self)
        m.setStyleSheet(
            "QMenu{background:#243244;color:#fff;border:1px solid rgba(255,255,255,.15);}"
            "QMenu::item{padding:7px 22px;}"
            "QMenu::item:selected{background:rgba(255,255,255,.15);}"
        )
        hdr = m.addAction("选择 AI（在右侧栏打开，自己登录即可）")
        hdr.setEnabled(False)
        m.addSeparator()
        for s in AI_SITES:
            a = m.addAction(s["name"])
            a.triggered.connect(lambda checked, n=s["name"]: self.open_ai_site(n))
        m.addSeparator()
        a = m.addAction("收起 / 展开侧边栏")
        a.triggered.connect(self.toggle_ai)
        m.exec(QCursor.pos())

    def open_ai_site(self, name):
        """在右侧栏打开某个 AI 网页版"""
        self.ai.show()
        total = self.splitter.width() or 1280
        self.splitter.setSizes([int(total * 0.72), int(total * 0.28)])
        self.ai_toggle.setText("✕")
        self.ai.open_site(name)

    def ask_ai_web(self, name, text):
        """右键选中文字：复制到剪贴板 + 侧边栏打开该 AI 网页版"""
        QApplication.clipboard().setText(text)
        self.open_ai_site(name)
        self.status.setText("已复制选中文字，粘贴到 %s 即可提问" % name)

    def _ensure_ai_width(self):
        total = self.splitter.width() or 1280
        self.splitter.setSizes([int(total * 0.72), int(total * 0.28)])

    def ask_ai(self, text):
        """走 API 对话模式（需密钥）"""
        self.ai.show()
        self._ensure_ai_width()
        self.ai_toggle.setText("✕")
        if self.ai.api_mode is False:
            self.ai.toggle_mode()
        self.ai.send(text)

    def toggle_ai(self):
        if self.ai.isVisible():
            self.ai.hide()
            self.ai_toggle.setText("✦")
        else:
            self.ai.show()
            self._ensure_ai_width()
            self.ai_toggle.setText("✕")

    # ---------- 菜单 ----------
    def open_feature_panel(self, tab="plugins"):
        dlg = FeaturePanel(self, tab)
        dlg.exec()

    def translate_page(self, text=""):
        """翻译：有选中文字 → 文本翻译页；否则把当前网页 URL 交给整页翻译。"""
        eng = self.settings.get("translate_engine", "baidu")
        if text:
            self.add_tab(translate_url("text", text, eng))
            return
        url = ""
        tab = self.current_tab()
        if tab:
            url = tab.url().toString()
        if not url.startswith(("http://", "https://")):
            self.status.setText("当前页面无法翻译")
            return
        self.add_tab(translate_url("page", url, eng))

    def set_translate_engine(self, key):
        self.settings["translate_engine"] = key
        save_settings(self.settings)
        self.status.setText(t("status.translator", name=translator_name(key)))

    def set_language(self, code):
        """切换界面语言（即时生效，部分控件需重开面板）。"""
        code = i18n.set_lang(code)
        self.settings["language"] = code
        save_settings(self.settings)
        self.refresh_newtabs()
        self.status.setText(t("status.lang_changed", name=i18n.lang_name(code)))

    def download_page_html(self):
        """把当前网页的 HTML 保存到本地下载目录。"""
        tab = self.current_tab()
        if not tab:
            return
        url = tab.url().toString()
        name = QUrl(url).host() or "page"
        safe = "".join(c for c in name if c.isalnum() or c in "-_.")[:40] or "page"
        dl_dir = os.path.join(data_dir(), "downloads")
        try:
            os.makedirs(dl_dir, exist_ok=True)
        except Exception:
            dl_dir = data_dir()
        path, _ = QFileDialog.getSaveFileName(self, "保存网页 HTML", os.path.join(dl_dir, safe + ".html"),
                                              "HTML 文件 (*.html *.htm)")
        if not path:
            return
        def _save(html):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                self.status.setText("已保存：" + path)
                # 记入下载历史
                try:
                    d = _load_settings_file("aqua_downloads.json")
                    if not isinstance(d, list):
                        d = []
                    d.insert(0, {"name": os.path.basename(path), "path": path,
                                 "time": time.strftime("%Y-%m-%d %H:%M:%S")})
                    with open(os.path.join(data_dir(), "aqua_downloads.json"), "w", encoding="utf-8") as f:
                        json.dump(d[:200], f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            except Exception as e:
                self.status.setText("保存失败：" + str(e))
        tab.page().toHtml(_save)

    def open_download_folder(self):
        d = os.path.join(data_dir(), "downloads")
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def open_themes_folder(self):
        """打开主题文件夹（用户可自己往里面丢 .json 主题）。"""
        d = themes_dir(self.settings)
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        self.status.setText("主题文件夹：" + d)

    def choose_themes_dir(self):
        """让用户指定主题文件夹位置（C 盘或 D 盘任意目录）。"""
        cur = themes_dir(self.settings)
        d = QFileDialog.getExistingDirectory(self, "选择主题文件夹", cur)
        if not d:
            return
        self.settings["themes_dir"] = d
        save_settings(self.settings)
        self.refresh_newtabs()
        self.status.setText("主题文件夹已设为：" + d)

    def reload_themes(self):
        """重新扫描主题目录并刷新界面。"""
        self.refresh_newtabs()
        self._apply_theme()
        n = len(load_theme_files(self.settings))
        self.status.setText("已加载 %d 个主题文件" % n)

    def set_search_engine(self, key):
        """切换默认搜索引擎：地址栏/新标签页/右键搜索统一生效。"""
        self.settings["search_engine"] = key
        save_settings(self.settings)
        self.refresh_newtabs()
        name = key
        for k, nm, _tpl in SEARCH_ENGINES:
            if k == key:
                name = nm; break
        self.status.setText(t("status.engine", name=name))

    def show_menu(self):
        self.build_menu().exec(QCursor.pos())

    def build_menu(self):
        """构建 ☰ 菜单（拆出来便于测试，exec 由调用方负责）。"""
        m = QMenu(self)
        p = palette_for(self.settings)
        m.setStyleSheet(
            "QMenu{background:%s;color:%s;border:1px solid %s;border-radius:12px;"
            "padding:6px 3px;}"
            "QMenu::item{padding:8px 24px;font-size:13px;border-radius:7px;"
            "background:transparent;}"
            "QMenu::item:selected{background:%s;color:#fff;}"
            "QMenu::item:disabled{color:%s;}"
            "QMenu::separator{height:1px;background:%s;margin:5px 8px;}"
            % (p["menu_bg"], p["text"], p["line"], p["accent"],
               p["text2"], p["line"])
        )
        # 搜索引擎子菜单
        eng_menu = m.addMenu(t("menu.search_engines"))
        cur_eng = self.settings.get("search_engine", "baidu")
        for k, name, _tpl in SEARCH_ENGINES:
            a = eng_menu.addAction(("✓ " if k == cur_eng else "   ") + name)
            a.setCheckable(True); a.setChecked(k == cur_eng)
            a.triggered.connect(lambda checked, ek=k: self.set_search_engine(ek))
        # 翻译子菜单（默认百度翻译，国内直连不用梯子）
        tr_menu = m.addMenu(t("menu.translate"))
        cur_tr = self.settings.get("translate_engine", "baidu")
        tr_menu.addAction(t("menu.translate_page", engine=translator_name(cur_tr)),
                          lambda: self.translate_page())
        tr_menu.addSeparator()
        for k, name, _pt, _tt in TRANSLATORS:
            a = tr_menu.addAction(("✓ " if k == cur_tr else "   ") + name)
            a.setCheckable(True)
            a.setChecked(k == cur_tr)
            a.triggered.connect(lambda checked, ek=k: self.set_translate_engine(ek))
        m.addSeparator()
        m.addAction(t("menu.plugins"), lambda: self.open_feature_panel("plugins"))
        m.addAction(t("menu.store"), lambda: self.open_feature_panel("store"))
        m.addAction(t("menu.appearance"), lambda: self.open_feature_panel("theme"))
        m.addAction(t("menu.themes_folder"), self.open_themes_folder)
        m.addAction(t("menu.choose_themes_dir"), self.choose_themes_dir)
        m.addAction(t("menu.reload_themes"), self.reload_themes)
        m.addSeparator()
        m.addAction(t("menu.bookmarks"), lambda: self.open_feature_panel("bookmarks"))
        m.addAction(t("menu.history"), lambda: self.open_feature_panel("history"))
        m.addAction(t("menu.downloads"), lambda: self.open_feature_panel("downloads"))
        m.addSeparator()
        ab = m.addAction(t("menu.adblock", state=t("state.on") if self.blocker.enabled else t("state.off")))
        ab.triggered.connect(self.toggle_adblock)
        dm = m.addAction(t("menu.darkmode", state=t("state.on") if self.settings["plugins"]["darkmode"] else t("state.off")))
        dm.triggered.connect(self.toggle_darkmode)
        m.addSeparator()
        m.addAction(t("menu.ai_settings"), self.open_ai_settings)
        # 语言子菜单
        lang_menu = m.addMenu(t("menu.language"))
        cur_lang = self.settings.get("language", i18n.DEFAULT_LANG)
        for code, name in i18n.LANGS:
            a = lang_menu.addAction(("✓ " if code == cur_lang else "   ") + name)
            a.setCheckable(True)
            a.setChecked(code == cur_lang)
            a.triggered.connect(lambda checked, c=code: self.set_language(c))
        m.addAction(t("menu.about", ver=VER), self.show_about)
        return m

    def toggle_adblock(self):
        on = not self.blocker.enabled
        self.blocker.set_enabled(on)
        self.settings["plugins"]["adblock"] = on
        save_settings(self.settings)
        QMessageBox.information(self, "广告拦截", "已%s（本次累计拦截 %d 个请求）" % ("开启" if on else "关闭", self.blocker.blocked))

    def toggle_darkmode(self):
        on = not self.settings["plugins"]["darkmode"]
        self.settings["plugins"]["darkmode"] = on
        save_settings(self.settings)
        for i in range(self.tabs.count()):
            v = self.tabs.widget(i)
            if isinstance(v, BrowserTab):
                if on:
                    v.apply_dark_mode()
                else:
                    v.clear_dark_mode()
        QMessageBox.information(self, "网页暗色模式",
                                "已%s。仅让网页内容变暗，浏览器界面始终保持明亮外观。" % ("开启" if on else "关闭"))

    def open_ai_settings(self):
        d = QDialog(self)
        d.setWindowTitle("AI 设置")
        d.setMinimumWidth(460)
        f = QFormLayout(d)
        ai = self.settings["ai"]

        preset = QComboBox()
        preset.addItems([p["name"] for p in AI_PRESETS] + ["自定义"])
        if ai.get("preset") in [p["name"] for p in AI_PRESETS]:
            preset.setCurrentText(ai["preset"])
        else:
            preset.setCurrentText("自定义")
        endpoint = QLineEdit(ai.get("endpoint", ""))
        model = QLineEdit(ai.get("model", ""))
        key = QLineEdit(ai.get("api_key", ""))
        key.setEchoMode(QLineEdit.Password)

        def on_preset(name):
            for p in AI_PRESETS:
                if p["name"] == name:
                    endpoint.setText(p["endpoint"])
                    model.setText(p["model"])
                    return
        preset.currentTextChanged.connect(on_preset)

        f.addRow("服务商", preset)
        f.addRow("接口地址", endpoint)
        f.addRow("模型", model)
        f.addRow("API 密钥", key)
        tip = QLabel("密钥只保存在本机 aqua_qt_settings.json，不会上传到任何第三方。\n"
                     "留空可用于本地 Ollama。支持任何 OpenAI 兼容接口。")
        tip.setStyleSheet("color:rgba(128,128,128,.9);font-size:11px;")
        f.addRow(tip)

        row = QHBoxLayout()
        okb = QPushButton("保存")
        cancel = QPushButton("取消")
        row.addWidget(okb)
        row.addWidget(cancel)
        f.addRow(row)

        def do_save():
            self.settings["ai"] = {
                "preset": preset.currentText(),
                "endpoint": endpoint.text().strip(),
                "model": model.text().strip(),
                "api_key": key.text().strip(),
            }
            save_settings(self.settings)
            self.ai.refresh_provider()
            d.accept()
        okb.clicked.connect(do_save)
        cancel.clicked.connect(d.reject)
        d.exec()

    def show_about(self):
        """关于：突出显示版本号与创作者视频号。"""
        p = palette_for(self.settings)
        box = QMessageBox(self)
        box.setWindowTitle("关于 " + APP_NAME)
        box.setIcon(QMessageBox.Icon.Information)
        box.setTextFormat(Qt.TextFormat.RichText)
        ch = (CREATOR_CHANNEL or "（未填写）")
        ch_id = ("（ID：%s）" % CREATOR_CHANNEL_ID) if CREATOR_CHANNEL_ID else ""
        repo = ('<p style="color:%s;">%s</p>' % (p["text2"], t("about.repo", url=PROJECT_URL))) if PROJECT_URL and PROJECT_URL.rstrip("/") != "https://github.com" else ""
        box.setText(
            "<h2 style='margin:0 0 6px 0;'>%s</h2>"
            "<p style='font-size:16px;margin:2px 0 10px 0;'><b>%s：%s</b></p>"
            "<table cellspacing='0' cellpadding='3'>"
            "<tr><td style='color:%s;'>%s</td><td><b>%s</b></td></tr>"
            "<tr><td style='color:%s;'>%s</td><td><b>%s</b> %s</td></tr>"
            "</table>"
            "<p style='margin-top:10px;'>%s<br>%s</p>"
            "<p style='color:%s;'>%s</p>"
            % (APP_NAME, t("about.version"), VER,
               p["text2"], t("about.creator"), CREATOR_NAME,
               p["text2"], t("about.channel"), ch, ch_id,
               t("about.desc1"), t("about.desc2"),
               p["text2"], t("about.core"))
            + repo
        )
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

    def closeEvent(self, event):
        save_settings(self.settings)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # 语言：启动时按设置载入（默认简体中文）
    try:
        i18n.set_lang(load_settings().get("language", i18n.DEFAULT_LANG))
    except Exception:
        pass
    # 应用级无衬线字体栈 + 全局弹层样式（QMenu/QToolTip/滚动条/对话框）
    _font = QFont()
    try:
        _font.setFamilies(FONT_FAMILIES)
    except Exception:
        _font.setFamily("Segoe UI")
    _font.setPointSize(10)
    app.setFont(_font)
    try:
        _s = load_settings()
        app.setStyleSheet(aqua_global_qss(palette_for(_s)))
    except Exception:
        app.setStyleSheet(aqua_global_qss(aqua_palette(210)))
    icon_path = os.path.join(app_dir(), "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    start = ""
    args = sys.argv[1:]
    if "--url" in args:
        i = args.index("--url")
        if i + 1 < len(args):
            u = args[i + 1]
            if u.lower().startswith(("http://", "https://")):
                start = u

    w = BrowserWindow(start)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
