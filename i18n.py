# -*- coding: utf-8 -*-
"""
微尽索浏览器 · 多语言
=====================
用法：
    import i18n
    i18n.set_lang("en")          # zh-CN / zh-TW / en
    i18n.t("menu.about")         # 取当前语言文案

新增语言：在 LANGS 里加一项，并在每个词条里补上对应 code 的译文即可。
缺译文时自动回退到简体中文，再缺则回退到词条 key（不会崩）。
"""

LANGS = [
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁體中文"),
    ("en", "English"),
]

DEFAULT_LANG = "zh-CN"
_current = DEFAULT_LANG


def set_lang(code):
    global _current
    if any(code == c for c, _ in LANGS):
        _current = code
    return _current


def get_lang():
    return _current


def lang_name(code=None):
    code = code or _current
    for c, n in LANGS:
        if c == code:
            return n
    return LANGS[0][1]


def t(key, **kw):
    row = S.get(key)
    if not row:
        return key
    txt = row.get(_current) or row.get(DEFAULT_LANG) or key
    if kw:
        try:
            txt = txt.format(**kw)
        except Exception:
            pass
    return txt


# ============================================================
# 词条表
# ============================================================
S = {
    # ---------- 主菜单 ----------
    "menu.search_engines": {"zh-CN": "🔍 搜索引擎", "zh-TW": "🔍 搜尋引擎", "en": "🔍 Search Engine"},
    "menu.translate": {"zh-CN": "🌐 翻译", "zh-TW": "🌐 翻譯", "en": "🌐 Translate"},
    "menu.translate_page": {"zh-CN": "翻译当前网页（{engine}）", "zh-TW": "翻譯目前網頁（{engine}）", "en": "Translate this page ({engine})"},
    "menu.plugins": {"zh-CN": "🧩 插件管理…", "zh-TW": "🧩 外掛管理…", "en": "🧩 Plugins…"},
    "menu.store": {"zh-CN": "🛒 插件商店…", "zh-TW": "🛒 外掛商店…", "en": "🛒 Plugin Store…"},
    "menu.appearance": {"zh-CN": "🎨 界面外观…", "zh-TW": "🎨 介面外觀…", "en": "🎨 Appearance…"},
    "menu.themes_folder": {"zh-CN": "🖼 主题文件夹…", "zh-TW": "🖼 主題資料夾…", "en": "🖼 Theme Folder…"},
    "menu.choose_themes_dir": {"zh-CN": "📂 选择主题目录…", "zh-TW": "📂 選擇主題目錄…", "en": "📂 Choose Theme Folder…"},
    "menu.reload_themes": {"zh-CN": "🔄 重新加载主题", "zh-TW": "🔄 重新載入主題", "en": "🔄 Reload Themes"},
    "menu.bookmarks": {"zh-CN": "🔖 书签管理…", "zh-TW": "🔖 書籤管理…", "en": "🔖 Bookmarks…"},
    "menu.history": {"zh-CN": "🕘 历史记录…", "zh-TW": "🕘 歷史紀錄…", "en": "🕘 History…"},
    "menu.downloads": {"zh-CN": "⬇ 下载管理…", "zh-TW": "⬇ 下載管理…", "en": "⬇ Downloads…"},
    "menu.adblock": {"zh-CN": "广告拦截：{state}", "zh-TW": "廣告攔截：{state}", "en": "Ad Block: {state}"},
    "menu.darkmode": {"zh-CN": "网页暗色模式（仅网页，不改界面）：{state}", "zh-TW": "網頁暗色模式（僅網頁，不改介面）：{state}", "en": "Dark Web Pages (page only): {state}"},
    "menu.ai_settings": {"zh-CN": "AI 设置…", "zh-TW": "AI 設定…", "en": "AI Settings…"},
    "menu.about": {"zh-CN": "关于 {ver}", "zh-TW": "關於 {ver}", "en": "About {ver}"},
    "menu.language": {"zh-CN": "🌏 语言", "zh-TW": "🌏 語言", "en": "🌏 Language"},
    "state.on": {"zh-CN": "已开启", "zh-TW": "已開啟", "en": "On"},
    "state.off": {"zh-CN": "已关闭", "zh-TW": "已關閉", "en": "Off"},

    # ---------- 功能面板导航 ----------
    "nav.plugins": {"zh-CN": "插件管理", "zh-TW": "外掛管理", "en": "Plugins"},
    "nav.store": {"zh-CN": "插件商店", "zh-TW": "外掛商店", "en": "Store"},
    "nav.theme": {"zh-CN": "界面外观", "zh-TW": "介面外觀", "en": "Appearance"},
    "nav.bookmarks": {"zh-CN": "书签", "zh-TW": "書籤", "en": "Bookmarks"},
    "nav.history": {"zh-CN": "历史", "zh-TW": "歷史", "en": "History"},
    "nav.downloads": {"zh-CN": "下载", "zh-TW": "下載", "en": "Downloads"},

    # ---------- 外观面板 ----------
    "theme.default_search": {"zh-CN": "默认搜索引擎", "zh-TW": "預設搜尋引擎", "en": "Default search engine"},
    "theme.default_translate": {"zh-CN": "默认翻译引擎", "zh-TW": "預設翻譯引擎", "en": "Default translator"},
    "theme.ui_color": {"zh-CN": "界面颜色（点击即时生效）", "zh-TW": "介面顏色（點擊即時生效）", "en": "UI color (instant)"},
    "theme.opacity": {"zh-CN": "不透明度", "zh-TW": "不透明度", "en": "Opacity"},
    "theme.blur": {"zh-CN": "毛玻璃模糊", "zh-TW": "毛玻璃模糊", "en": "Blur"},
    "theme.newtab_bg": {"zh-CN": "标签页背景（内置 + 主题文件，点击即时生效）", "zh-TW": "分頁背景（內建 + 主題檔案，點擊即時生效）", "en": "Tab background (built-in + theme files)"},
    "theme.open_folder": {"zh-CN": "打开主题文件夹", "zh-TW": "開啟主題資料夾", "en": "Open theme folder"},
    "theme.choose_dir": {"zh-CN": "选择主题目录…", "zh-TW": "選擇主題目錄…", "en": "Choose folder…"},
    "theme.reload": {"zh-CN": "重新加载", "zh-TW": "重新載入", "en": "Reload"},
    "theme.dir_hint": {"zh-CN": "主题目录：{dir}　（{n} 个主题文件）", "zh-TW": "主題目錄：{dir}　（{n} 個主題檔案）", "en": "Theme folder: {dir}  ({n} themes)"},
    "theme.plugin_on": {"zh-CN": "开", "zh-TW": "開", "en": "On"},
    "theme.plugin_off": {"zh-CN": "关", "zh-TW": "關", "en": "Off"},

    # ---------- 关于 ----------
    "about.version": {"zh-CN": "版本号", "zh-TW": "版本號", "en": "Version"},
    "about.creator": {"zh-CN": "创作者", "zh-TW": "創作者", "en": "Creator"},
    "about.channel": {"zh-CN": "视频号", "zh-TW": "視頻號", "en": "WeChat Channel"},
    "about.desc1": {"zh-CN": "基于 PySide6 + QtWebEngine（内置 Chromium 内核）", "zh-TW": "基於 PySide6 + QtWebEngine（內建 Chromium 核心）", "en": "Built on PySide6 + QtWebEngine (bundled Chromium)"},
    "about.desc2": {"zh-CN": "真·多标签 · 原生右键 · 真实插件 · AI 助手 · 主题包", "zh-TW": "真·多分頁 · 原生右鍵 · 真實外掛 · AI 助手 · 主題包", "en": "True multi-tab · native context menu · real plugins · AI panel · theme packs"},
    "about.core": {"zh-CN": "内核随程序打包，无需系统安装 Edge。", "zh-TW": "核心隨程式打包，無需系統安裝 Edge。", "en": "The engine ships with the app — no Edge required."},
    "about.repo": {"zh-CN": "开源仓库：{url}", "zh-TW": "開源倉庫：{url}", "en": "Repository: {url}"},

    # ---------- 状态提示 ----------
    "status.engine": {"zh-CN": "默认搜索引擎已设为：{name}", "zh-TW": "預設搜尋引擎已設為：{name}", "en": "Default search engine: {name}"},
    "status.translator": {"zh-CN": "翻译引擎已切换为：{name}", "zh-TW": "翻譯引擎已切換為：{name}", "en": "Translator: {name}"},
    "status.themes_folder": {"zh-CN": "主题文件夹：{dir}", "zh-TW": "主題資料夾：{dir}", "en": "Theme folder: {dir}"},
    "status.themes_loaded": {"zh-CN": "已加载 {n} 个主题文件", "zh-TW": "已載入 {n} 個主題檔案", "en": "Loaded {n} theme files"},
    "status.lang_changed": {"zh-CN": "语言已切换为：{name}（重启后完全生效）", "zh-TW": "語言已切換為：{name}（重啟後完全生效）", "en": "Language: {name} (restart to apply fully)"},

    # ---------- 新标签页 ----------
    "nt.badge": {"zh-CN": "插件 · 安全 · 自由 · AI", "zh-TW": "外掛 · 安全 · 自由 · AI", "en": "Plugins · Secure · Free · AI"},
    "nt.search_btn": {"zh-CN": "搜索", "zh-TW": "搜尋", "en": "Search"},
    "nt.search_ph": {"zh-CN": "搜索或输入网址，回车打开…", "zh-TW": "搜尋或輸入網址，按 Enter 開啟…", "en": "Search or enter address, press Enter…"},
    "nt.quick": {"zh-CN": "快捷访问", "zh-TW": "快速存取", "en": "Quick access"},
    "nt.tools": {"zh-CN": "常用工具", "zh-TW": "常用工具", "en": "Tools"},
    "nt.appearance": {"zh-CN": "外观", "zh-TW": "外觀", "en": "Appearance"},
    "nt.opacity": {"zh-CN": "不透明度", "zh-TW": "不透明度", "en": "Opacity"},
    "nt.blur": {"zh-CN": "毛玻璃", "zh-TW": "毛玻璃", "en": "Blur"},
    "nt.custom_bg": {"zh-CN": "自定义背景", "zh-TW": "自訂背景", "en": "Custom background"},
    "nt.solid": {"zh-CN": "纯色", "zh-TW": "單色", "en": "Solid"},
    "nt.apply": {"zh-CN": "应用", "zh-TW": "套用", "en": "Apply"},
    "nt.follow": {"zh-CN": "玻璃跟随背景", "zh-TW": "玻璃跟隨背景", "en": "Glass follows background"},
    "nt.follow_on": {"zh-CN": "开", "zh-TW": "開", "en": "On"},
    "nt.follow_off": {"zh-CN": "关", "zh-TW": "關", "en": "Off"},
    "nt.welcome": {"zh-CN": "欢迎回来", "zh-TW": "歡迎回來", "en": "Welcome back"},
}
