#!/usr/bin/env bash
# Build ScreenOffTimer-x86_64.AppImage using linuxdeploy + gtk plugin.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ARCH="${ARCH:-x86_64}"
TOOLS_DIR="$ROOT/.build/tools"
APPDIR="$ROOT/AppDir"
OUTPUT_NAME="ScreenOffTimer-${ARCH}.AppImage"

LINUXDEPLOY="$TOOLS_DIR/linuxdeploy-${ARCH}.AppImage"
PLUGIN_GTK="$TOOLS_DIR/linuxdeploy-plugin-gtk.sh"

download_file() {
    local name="$1"
    local url="$2"
    local dest="$3"
    if [[ -f "$dest" ]] && [[ -s "$dest" ]]; then
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    echo "Downloading $name ..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --retry 5 --retry-delay 2 -o "$dest" "$url"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$dest" "$url"
    else
        echo "Need curl or wget to download $name" >&2
        exit 1
    fi
}

case "$ARCH" in
    x86_64)
        LINUXDEPLOY_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
        ;;
    aarch64)
        LINUXDEPLOY_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-aarch64.AppImage"
        ;;
    *)
        echo "Unsupported ARCH=$ARCH" >&2
        exit 1
        ;;
esac

download_file "linuxdeploy" "$LINUXDEPLOY_URL" "$LINUXDEPLOY"
chmod +x "$LINUXDEPLOY"

download_file "linuxdeploy-plugin-gtk" \
    "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh" \
    "$PLUGIN_GTK"
chmod +x "$PLUGIN_GTK"

export PATH="$TOOLS_DIR:$PATH"
export DEPLOY_GTK_VERSION="${DEPLOY_GTK_VERSION:-4}"
export APPIMAGE_EXTRACT_AND_RUN=1

# Regenerate circular icons if generator is available.
if [[ -f "$ROOT/scripts/generate_icon.py" ]]; then
    python3 "$ROOT/scripts/generate_icon.py"
fi

ICON_FILE="$ROOT/data/icons/hicolor/256x256/apps/screen-off-timer.png"
if [[ ! -f "$ICON_FILE" ]]; then
    ICON_FILE="$ROOT/data/icons/hicolor/48x48/apps/screen-off-timer.png"
fi

# --- AppDir layout ---
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib/screen-off-timer" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/48x48/apps"

cp -a "$ROOT/src/." "$APPDIR/usr/lib/screen-off-timer/"
cp "$ROOT/data/com.example.ScreenOffTimer.desktop" "$APPDIR/usr/share/applications/"
cp "$ROOT/data/icons/hicolor/48x48/apps/screen-off-timer.png" \
    "$APPDIR/usr/share/icons/hicolor/48x48/apps/"

# Entry binary: system python3 (linuxdeploy bundles interpreter + base libs).
cp -L "$(command -v python3)" "$APPDIR/usr/bin/python3"
chmod +x "$APPDIR/usr/bin/python3"

if command -v xset >/dev/null 2>&1; then
    cp -L "$(command -v xset)" "$APPDIR/usr/bin/xset"
fi
if command -v wlr-dpms >/dev/null 2>&1; then
    cp -L "$(command -v wlr-dpms)" "$APPDIR/usr/bin/wlr-dpms"
fi

# Desktop Exec=screen-off-timer — must exist before linuxdeploy deploys root symlinks.
cat >"$APPDIR/usr/bin/screen-off-timer" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
export PATH="${HERE}:${PATH}"
export PYTHONPATH="${HERE}/../lib/screen-off-timer${PYTHONPATH:+:${PYTHONPATH}}"
exec "${HERE}/python3" "${HERE}/../lib/screen-off-timer/main.py" "$@"
LAUNCHER
chmod +x "$APPDIR/usr/bin/screen-off-timer"

export LINUXDEPLOY="$LINUXDEPLOY"

# GTK plugin script must sit beside linuxdeploy AppImage (already in TOOLS_DIR).
"$LINUXDEPLOY" \
    --appdir "$APPDIR" \
    --executable "$APPDIR/usr/bin/python3" \
    --desktop-file "$ROOT/data/com.example.ScreenOffTimer.desktop" \
    --icon-file "$ICON_FILE" \
    --plugin gtk

# Bundle PyGObject + typelibs (not linked into python3 ELF).
PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
DEST="$APPDIR/usr/lib/python${PYVER}/site-packages"
mkdir -p "$DEST"
for site in /usr/lib/python3/dist-packages /usr/lib/python"${PYVER%.*}"/dist-packages \
    "/usr/lib/python${PYVER}/site-packages"; do
    [[ -d "$site/gi" ]] || continue
    cp -a "$site/gi" "$DEST/"
    for mod in cairo _cairo; do
        compgen -G "$site/${mod}*" >/dev/null 2>&1 && cp -a "$site/${mod}"* "$DEST/" || true
    done
done

mkdir -p "$APPDIR/usr/lib/girepository-1.0" "$APPDIR/usr/lib/x86_64-linux-gnu/girepository-1.0"
for repo in /usr/lib/x86_64-linux-gnu/girepository-1.0 /usr/lib/girepository-1.0; do
    [[ -d "$repo" ]] || continue
    cp -a "$repo"/*.typelib "$APPDIR/usr/lib/x86_64-linux-gnu/girepository-1.0/" 2>/dev/null || true
done

# AppRun: launch application with bundled Python + GI paths.
cat >"$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/screen-off-timer${PYTHONPATH:+:${PYTHONPATH}}"
export GI_TYPELIB_PATH="${HERE}/usr/lib/girepository-1.0:${HERE}/usr/lib/x86_64-linux-gnu/girepository-1.0${GI_TYPELIB_PATH:+:${GI_TYPELIB_PATH}}"
export GSETTINGS_SCHEMA_DIR="${HERE}/usr/share/glib-2.0/schemas${GSETTINGS_SCHEMA_DIR:+:${GSETTINGS_SCHEMA_DIR}}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
exec "${HERE}/usr/bin/screen-off-timer" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

APPIMAGETOOL="$TOOLS_DIR/appimagetool-${ARCH}.AppImage"
download_file "appimagetool" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
    "$APPIMAGETOOL"
chmod +x "$APPIMAGETOOL"
rm -f "$ROOT/$OUTPUT_NAME"
ARCH="$ARCH" "$APPIMAGETOOL" "$APPDIR" "$ROOT/$OUTPUT_NAME"

chmod +x "$ROOT/$OUTPUT_NAME"
echo ""
echo "Built: $ROOT/$OUTPUT_NAME"
ls -lh "$ROOT/$OUTPUT_NAME"
