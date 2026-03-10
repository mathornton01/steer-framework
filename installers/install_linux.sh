#!/bin/bash
# =================================================================================================
# STEER Framework — Linux Installer
# =================================================================================================
# This script sets up the STEER Framework on Linux, including:
#   - System dependency checks
#   - Python dependency installation
#   - C test compilation
#   - Desktop entry creation
#   - CLI tool installation
# =================================================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "================================================================================"
echo "  STEER Framework Installer for Linux"
echo "================================================================================"
echo ""

# Color output helpers
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detect package manager
PKG_MGR=""
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
elif command -v zypper &>/dev/null; then
    PKG_MGR="zypper"
fi

install_system_deps() {
    echo "Installing system dependencies..."
    case "$PKG_MGR" in
        apt)
            sudo apt-get update -qq
            sudo apt-get install -y -qq python3 python3-pip python3-venv gcc make
            ;;
        dnf)
            sudo dnf install -y python3 python3-pip gcc make
            ;;
        pacman)
            sudo pacman -S --noconfirm python python-pip gcc make
            ;;
        zypper)
            sudo zypper install -y python3 python3-pip gcc make
            ;;
        *)
            warn "Unknown package manager. Please install manually: python3, pip, gcc, make"
            ;;
    esac
}

# Check Python 3
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    ok "Found Python $PYVER"
else
    warn "Python 3 not found."
    if [ -n "$PKG_MGR" ]; then
        install_system_deps
    else
        fail "Please install Python 3.10+ and re-run."
        exit 1
    fi
fi

# Check GCC and Make
if command -v gcc &>/dev/null && command -v make &>/dev/null; then
    ok "Build tools (gcc, make) found."
else
    warn "Build tools missing."
    if [ -n "$PKG_MGR" ]; then
        install_system_deps
    else
        warn "Please install gcc and make."
    fi
fi

echo ""
ok "Framework root: $FRAMEWORK_ROOT"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."

# Try regular pip first, then --user, then --break-system-packages
python3 -m pip install PyQt6 numpy pandas scikit-learn scipy 2>/dev/null || \
python3 -m pip install --user PyQt6 numpy pandas scikit-learn scipy 2>/dev/null || \
python3 -m pip install --user --break-system-packages PyQt6 numpy pandas scikit-learn scipy 2>/dev/null || {
    warn "pip install failed. You may need to install packages manually."
    warn "Try: python3 -m pip install --user PyQt6 numpy pandas scikit-learn scipy"
}
ok "Python dependencies installed."

# Build STEER C tests
echo ""
echo "Building STEER C tests..."
cd "$FRAMEWORK_ROOT"
if [ -f "build.sh" ]; then
    bash build.sh && ok "STEER C tests built successfully." || warn "Build had errors (see above)."
else
    warn "build.sh not found. Skipping C test build."
fi

# Create launcher scripts
echo ""
echo "Creating launcher scripts..."

LAUNCHER="$FRAMEWORK_ROOT/steer-gui"
cat > "$LAUNCHER" << 'LAUNCHEOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/src/steer-gui"
exec python3 main.py --root "$SCRIPT_DIR" "$@"
LAUNCHEOF
chmod +x "$LAUNCHER"
ok "GUI launcher: $LAUNCHER"

DOCS_LAUNCHER="$FRAMEWORK_ROOT/steer-docs"
cat > "$DOCS_LAUNCHER" << 'DOCSEOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/src/steer-docs/steer_docs.py" "$@"
DOCSEOF
chmod +x "$DOCS_LAUNCHER"
ok "Docs CLI: $DOCS_LAUNCHER"

# Create desktop entry
echo ""
echo "Creating desktop entry..."

DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESKTOP_DIR"

LOGO="$FRAMEWORK_ROOT/src/steer-gui/resources/steer-blue-logo.png"
ICON_PATH=""
if [ -f "$LOGO" ]; then
    ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
    mkdir -p "$ICON_DIR"
    cp "$LOGO" "$ICON_DIR/steer-framework.png"
    ICON_PATH="$ICON_DIR/steer-framework.png"
fi

cat > "$DESKTOP_DIR/steer-framework.desktop" << DESKTOPEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=STEER Framework
Comment=Statistical Testing of Entropy and Evaluation of Randomness
Exec=$LAUNCHER
Icon=${ICON_PATH:-utilities-terminal}
Terminal=false
Categories=Science;Math;Education;
Keywords=NIST;randomness;entropy;testing;statistics;
StartupNotify=true
DESKTOPEOF

chmod +x "$DESKTOP_DIR/steer-framework.desktop"
ok "Desktop entry created: $DESKTOP_DIR/steer-framework.desktop"

# Optional: symlink to ~/.local/bin
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    warn "$LOCAL_BIN is not in PATH. Add it to your shell profile:"
    warn "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
fi

ln -sf "$LAUNCHER" "$LOCAL_BIN/steer-gui"
ln -sf "$DOCS_LAUNCHER" "$LOCAL_BIN/steer-docs"
ok "Symlinks created in $LOCAL_BIN"

echo ""
echo "================================================================================"
echo "  Installation complete!"
echo "================================================================================"
echo ""
echo "  Launch GUI:        ./steer-gui  (or steer-gui if ~/.local/bin is in PATH)"
echo "  View docs (CLI):   ./steer-docs --list"
echo "  Desktop entry:     Search for 'STEER Framework' in your application menu"
echo ""
