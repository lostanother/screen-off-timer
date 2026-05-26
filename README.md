# 延时熄屏 (Screen Off Timer)

在图形界面中输入秒数，倒计时结束后关闭显示器。支持 **Linux**（X11 / GNOME / KDE / wlroots）与 **Windows 10+**。

## 用法

### Linux — 从源码运行

```bash
cd screen-off-timer/src
python3 main.py
```

依赖：`python3-gi`、`gir1.2-gtk-4.0`，以及当前环境对应的熄屏工具（见下表）。

### Windows — 从源码运行

需 **Python 3.10+**（自带 tkinter，安装时勾选 *tcl/tk*）：

```powershell
cd screen-off-timer\src
python run.py
```

或直接：

```powershell
python main_win.py
```

### AppImage

```bash
chmod +x ScreenOffTimer-x86_64.AppImage
./ScreenOffTimer-x86_64.AppImage
```

若系统未安装 FUSE，可使用：

```bash
./ScreenOffTimer-x86_64.AppImage --appimage-extract-and-run
```

## 支持的环境

### Linux

| 会话 | 检测条件 | 熄屏方式 |
|------|----------|----------|
| X11 | `XDG_SESSION_TYPE=x11` | `xset dpms force off`（AppImage 内捆绑 `xset`） |
| GNOME Wayland | 桌面名含 gnome/ubuntu/cinnamon 等 | `busctl` → Mutter `PowerSaveMode=3` |
| KDE Wayland | 桌面名含 kde/plasma | `kscreen-doctor --dpms off` |
| wlroots | sway/hyprland 等 | `wlr-dpms off` |

### Windows

| 平台 | 熄屏方式 |
|------|----------|
| Windows 10+ | `SendMessage(WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)` |

唤醒：移动鼠标或按键即可。

**不支持**：整机休眠/睡眠；Linux 上未知 Wayland 合成器会弹出错误说明。

## 构建 AppImage

构建机（Debian/Ubuntu 示例）：

```bash
# Ubuntu / Linux Mint（不要用 xorg-xset，那是 Arch 包名）
sudo apt install -y libgtk-4-dev python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gcc patchelf curl x11-xserver-utils
# 仅当运行 AppImage 提示缺少 FUSE 时再装（构建不必装 fuse 元包）：
# sudo apt install -y libfuse2t64
./build-appimage.sh
```

产物：`ScreenOffTimer-x86_64.AppImage`

## 构建 Windows exe

在 **Windows 10/11** 上构建（PyInstaller 无法跨平台生成 exe）：

```powershell
cd screen-off-timer
# 双击或在 PowerShell 中：
.\build-windows.bat
```

或：

```powershell
pip install -r requirements-windows.txt
python scripts\generate_icon.py
pyinstaller --noconfirm ScreenOffTimer.spec
```

产物：`dist\ScreenOffTimer.exe`（无控制台窗口，单文件）。

**要求**：已安装 [Python 3.10+](https://www.python.org/downloads/)，安装时勾选 *Add to PATH* 与 *tcl/tk*。

### 用 GitHub Actions 构建（无需 Windows 电脑）

1. 打开仓库 [Actions](https://github.com/lostanother/screen-off-timer/actions) 页
2. 选择 **Build Windows exe** → **Run workflow** → **Run workflow**
3. 运行结束后点进该次任务，在 **Artifacts** 中下载 `ScreenOffTimer-windows`（内含 `ScreenOffTimer.exe`）

推送到 `main` 分支且改动涉及源码时也会自动触发构建。

## Linux AppImage 可选环境变量

- `ARCH=aarch64` — 构建 ARM64 包（需对应架构构建机）
- `DEPLOY_GTK_VERSION=4` — GTK 版本（默认 4）

## 图标

圆形极简图标（明艳渐变 + 显示器 / 电源 / 倒计时圆点），可重新生成：

```bash
python3 scripts/generate_icon.py
```

输出：`data/icons/hicolor/*/apps/screen-off-timer.png`（16–256px）及 `screen-off-timer-master.png`（512px）。

## 项目结构

```
screen-off-timer/
├── src/
│   ├── run.py              # 跨平台入口
│   ├── main.py             # Linux GTK 4
│   ├── main_win.py         # Windows tkinter
│   ├── display.py          # 平台分发
│   ├── display_linux.py
│   └── display_windows.py
├── scripts/generate_icon.py
├── build-appimage.sh       # Linux
├── build-windows.ps1       # Windows
├── ScreenOffTimer.spec     # PyInstaller
└── data/icons/
```

## 许可证

MIT（可按需修改）
