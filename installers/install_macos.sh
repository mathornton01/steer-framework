#!/bin/bash
# =================================================================================================
# STEER Framework — macOS Installer
# =================================================================================================
# This script sets up the STEER Framework on macOS, including:
#   - Homebrew check and Python dependency installation
#   - C test compilation
#   - Application bundle creation
#   - CLI tool installation
# =================================================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "================================================================================"
echo "  STEER Framework Installer for macOS"
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

# Check for Homebrew
if command -v brew &>/dev/null; then
    ok "Homebrew found."
else
    warn "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ok "Homebrew installed."
fi

# Check for Python 3
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    ok "Found Python $PYVER"
else
    warn "Python 3 not found. Installing via Homebrew..."
    brew install python3
    ok "Python 3 installed."
fi

# Check for GCC/Make
if command -v gcc &>/dev/null && command -v make &>/dev/null; then
    ok "Build tools (gcc, make) found."
else
    warn "Build tools not found. Installing Xcode Command Line Tools..."
    xcode-select --install 2>/dev/null || true
    echo "  Please complete the Xcode Command Line Tools installation and re-run."
fi

echo ""
ok "Framework root: $FRAMEWORK_ROOT"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
python3 -m pip install --user PyQt6 numpy pandas scikit-learn scipy 2>/dev/null || {
    warn "pip install failed. Trying with --break-system-packages..."
    python3 -m pip install --user --break-system-packages PyQt6 numpy pandas scikit-learn scipy
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

# Create launcher script
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

# Create docs CLI launcher
DOCS_LAUNCHER="$FRAMEWORK_ROOT/steer-docs"
cat > "$DOCS_LAUNCHER" << 'DOCSEOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/src/steer-docs/steer_docs.py" "$@"
DOCSEOF
chmod +x "$DOCS_LAUNCHER"
ok "Docs CLI: $DOCS_LAUNCHER"

# Create macOS .app bundle
echo ""
echo "Creating macOS application bundle..."

APP_DIR="$FRAMEWORK_ROOT/STEER Framework.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

mkdir -p "$MACOS" "$RESOURCES"

# Info.plist
cat > "$CONTENTS/Info.plist" << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>STEER Framework</string>
    <key>CFBundleDisplayName</key>
    <string>STEER Framework</string>
    <key>CFBundleIdentifier</key>
    <string>org.steer.framework</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>steer-gui</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
</dict>
</plist>
PLISTEOF

# Executable wrapper
cat > "$MACOS/steer-gui" << APPEOF
#!/bin/bash
FRAMEWORK_ROOT="$FRAMEWORK_ROOT"
cd "\$FRAMEWORK_ROOT/src/steer-gui"
exec python3 main.py --root "\$FRAMEWORK_ROOT" "\$@"
APPEOF
chmod +x "$MACOS/steer-gui"

# Copy logo as icon (if available)
LOGO="$FRAMEWORK_ROOT/src/steer-gui/resources/steer-blue-logo.png"
if [ -f "$LOGO" ]; then
    cp "$LOGO" "$RESOURCES/steer-logo.png"
fi

ok "Application bundle: $APP_DIR"

# Symlink to /usr/local/bin (optional)
echo ""
read -p "  Add steer-gui and steer-docs to /usr/local/bin? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo ln -sf "$LAUNCHER" /usr/local/bin/steer-gui 2>/dev/null && ok "steer-gui linked to /usr/local/bin" || warn "Could not create symlink."
    sudo ln -sf "$DOCS_LAUNCHER" /usr/local/bin/steer-docs 2>/dev/null && ok "steer-docs linked to /usr/local/bin" || warn "Could not create symlink."
fi

echo ""
echo "================================================================================"
echo "  Installation complete!"
echo "================================================================================"
echo ""
echo "  Launch GUI:        ./steer-gui"
echo "  View docs (CLI):   ./steer-docs --list"
echo "  macOS App:         Open 'STEER Framework.app'"
echo ""
echo "  You can drag 'STEER Framework.app' to your Applications folder."
echo ""
