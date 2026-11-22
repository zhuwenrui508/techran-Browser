# -*- coding: utf-8 -*-
"""把 背景1.svg 渲染成应用图标：app_icon.png(512) + app_icon.ico(多尺寸)。"""
import os
import sys

from PySide6.QtCore import QSize, Qt, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

HERE = os.path.dirname(os.path.abspath(__file__))
SVG = r"C:\Users\aukam\OneDrive\Desktop\背景1.svg"

app = QGuiApplication(sys.argv)

# 1) 以 1024 见方的正方形画布居中渲染（图标必须正方形，留 8% 内边距）
SIDE = 1024
img = QImage(SIDE, SIDE, QImage.Format_ARGB32)
img.fill(Qt.transparent)

r = QSvgRenderer(SVG)
print("svg valid:", r.isValid(), "defaultSize:", r.defaultSize())
ds = r.defaultSize()
if not ds.isValid() or ds.isEmpty():
    ds = QSize(144, 112)
pad = int(SIDE * 0.08)
avail = SIDE - pad * 2
scale = min(avail / ds.width(), avail / ds.height())
w = ds.width() * scale
h = ds.height() * scale
target = QRectF((SIDE - w) / 2, (SIDE - h) / 2, w, h)

p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing, True)
p.setRenderHint(QPainter.SmoothPixmapTransform, True)
r.render(p, target)
p.end()

png512 = os.path.join(HERE, "app_icon_512.png")
img.save(png512)
print("saved", png512)

# 2) 缩放到 256 存 app_icon.png（窗口图标用）
img256 = img.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
png256 = os.path.join(HERE, "app_icon.png")
img256.save(png256)
print("saved", png256)

# 3) 多尺寸 .ico
try:
    from PIL import Image
    pil = Image.open(png512).convert("RGBA")
    ico = os.path.join(HERE, "app_icon.ico")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    pil.save(ico, format="ICO", sizes=sizes)
    print("saved", ico, os.path.getsize(ico), "bytes")
except Exception as e:
    print("ICO FAILED", e)
