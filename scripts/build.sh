#!/usr/bin/env bash
# Build script for c0lor-mem
# Usage: ./scripts/build.sh [win|mac|all]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_DIR="$PROJECT_DIR/python"

echo "=== c0lor-mem Build Script ==="

# Step 1: Build Python backend with PyInstaller
echo ""
echo "--- Building Python backend ---"
cd "$PYTHON_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]"
fi

.venv/bin/pip install pyinstaller 2>/dev/null
.venv/bin/pyinstaller backend.spec --clean --noconfirm
echo "Python backend built to: $PYTHON_DIR/dist/c0lor-mem-backend/"

# Step 2: Build Electron app
echo ""
echo "--- Building Electron app ---"
cd "$PROJECT_DIR"

npm run build

# Step 3: Package with electron-builder
echo ""
echo "--- Packaging ---"
TARGET="${1:-all}"

case "$TARGET" in
    win)
        npx electron-builder --win
        ;;
    mac)
        npx electron-builder --mac
        ;;
    all)
        npx electron-builder --win --mac
        ;;
    *)
        echo "Usage: $0 [win|mac|all]"
        exit 1
        ;;
esac

echo ""
echo "=== Build complete! ==="
echo "Output: $PROJECT_DIR/dist/"
