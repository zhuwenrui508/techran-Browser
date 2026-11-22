# -*- coding: utf-8 -*-
"""用 IShellLinkW COM 在真实桌面创建/更新快捷方式（图标取 EXE 内嵌图标）。"""
import ctypes
from ctypes import wintypes, c_void_p, POINTER, byref

EXE = r"D:\AquaBrowser\dist\v38\微尽索浏览器Qt\微尽索浏览器Qt.exe"
WORKDIR = r"D:\AquaBrowser\dist\v38\微尽索浏览器Qt"
LNK = r"C:\Users\aukam\OneDrive\Desktop\微尽索浏览器.lnk"

ole32 = ctypes.windll.ole32
CLSCTX_LOCAL_SERVER = 4


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_byte * 8)]


CLSID_ShellLink = GUID(0x00021401, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))
IID_IShellLinkW = GUID(0x000214F9, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))
IID_IPersistFile = GUID(0x0000010B, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))

ole32.CoInitialize(None)

link = c_void_p()
hr = ole32.CoCreateInstance(byref(CLSID_ShellLink), None, CLSCTX_LOCAL_SERVER,
                            byref(IID_IShellLinkW), byref(link))
print("CoCreateInstance hr=", hex(hr & 0xFFFFFFFF))
if hr < 0:
    raise SystemExit("create failed")

vt = ctypes.cast(link, POINTER(POINTER(c_void_p))).contents
LPCWSTR = ctypes.c_wchar_p


def call(idx, *sig):
    return ctypes.WINFUNCTYPE(ctypes.c_long, c_void_p, *sig)(vt[idx])


print("SetPath hr=", hex(call(5, LPCWSTR)(link, EXE) & 0xFFFFFFFF))
print("SetWorkingDirectory hr=", hex(call(9, LPCWSTR)(link, WORKDIR) & 0xFFFFFFFF))
print("SetDescription hr=", hex(call(7, LPCWSTR)(link, "微尽索浏览器 v3.8 - 浅色菜单") & 0xFFFFFFFF))
print("SetIconLocation hr=", hex(call(15, LPCWSTR, wintypes.INT)(link, EXE, 0) & 0xFFFFFFFF))

persist = c_void_p()
hr = ctypes.WINFUNCTYPE(ctypes.c_long, c_void_p, POINTER(GUID), POINTER(c_void_p))(vt[0])(
    link, byref(IID_IPersistFile), byref(persist))
print("QI IPersistFile hr=", hex(hr & 0xFFFFFFFF))
if hr < 0:
    raise SystemExit("QI failed")

pvt = ctypes.cast(persist, POINTER(POINTER(c_void_p))).contents
hr = ctypes.WINFUNCTYPE(ctypes.c_long, c_void_p, LPCWSTR, wintypes.BOOL)(pvt[6])(persist, LNK, True)
print("Save hr=", hex(hr & 0xFFFFFFFF))
print("SAVED:", LNK)

ctypes.WINFUNCTYPE(wintypes.ULONG, c_void_p)(pvt[2])(persist)
ctypes.WINFUNCTYPE(wintypes.ULONG, c_void_p)(vt[2])(link)
ole32.CoUninitialize()
