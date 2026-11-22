# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# 只收集 PySide6 的数据文件（含 WebEngine 的 icudtl.dat / *.pak / 翻译），
# 不 collect_all，避免把 Qt3D/QtCharts 等用不到的模块和调试 pdb 全带进来。
datas = [('app_icon.ico', '.'), ('app_icon.png', '.')]
datas += collect_data_files('PySide6', includes=['**/*.pak', '**/*.dat', '**/QtWebEngineProcess.exe'])
binaries = []
hiddenimports = ['PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore', 'PySide6.QtWebChannel']

a = Analysis(
    ['aqua_browser_qt.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.QtCharts',
              'PySide6.QtDataVisualization', 'PySide6.QtMultimedia',
              'PySide6.QtQuick', 'PySide6.QtQuick3D', 'PySide6.QtQml',
              'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning',
              'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtTest',
              'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtSql'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='微尽索浏览器Qt',
    icon='app_icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='微尽索浏览器Qt',
)
