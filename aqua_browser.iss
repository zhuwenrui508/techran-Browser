; ============================================================
; 微尽索浏览器 · Inno Setup 安装脚本
; 编译： "C:\Users\<你>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer\aqua_browser.iss
; 产物： installer\输出\微尽索浏览器-安装包-v3.8.exe
; ============================================================

#define AppName "微尽索浏览器"
#define AppNameEn "AquaBrowser"
#define AppVersion "3.8"
#define AppPublisher "微尽索"
#define AppExe "微尽索浏览器Qt.exe"
; 已打包好的程序目录（PyInstaller onedir 产物）
#define SrcDir "D:\AquaBrowser\dist\微尽索浏览器Qt"
; 主题包目录
#define ThemeDir "D:\AquaBrowser\src\themes"

[Setup]
AppId={{8E2C1B44-7A61-4C0E-9C2B-1F5D3A9E7B12}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}
DefaultDirName=D:\{#AppNameEn}
DefaultGroupName={#AppName}
; 允许用户自选安装盘（C 盘或 D 盘）
DisableDirPage=no
AllowNoIcons=yes
OutputDir=输出
OutputBaseFilename={#AppName}-安装包-v{#AppVersion}
SetupIconFile=D:\AquaBrowser\src\app_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0

[Languages]
Name: "zhcn"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
; ---- 主程序（整个 PyInstaller 目录）----
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; ---- 主题包 → {app}\themes ----
Source: "{#ThemeDir}\*.json"; DestDir: "{app}\themes"; Flags: ignoreversion
Source: "{#ThemeDir}\README-主题格式.md"; DestDir: "{app}\themes"; Flags: ignoreversion
; ---- 说明文档 ----
Source: "D:\AquaBrowser\src\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
; 桌面快捷方式（.lnk）—— 用户勾选才创建
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon
; 开始菜单
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\主题文件夹"; Filename: "{app}\themes"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "立即运行 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\themes"
Type: files; Name: "{app}\aqua_qt_settings.json"
