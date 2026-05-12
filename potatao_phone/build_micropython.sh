#!/bin/bash
set -e

# ─────────────────────────────────────────
# CONFIGURATION — change this to switch boards
BOARD_MODEL="pico2_w"
# ─────────────────────────────────────────

# Portable "realpath" function for macOS/Linux compatibility
get_abspath() {
    echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

# Auto-set the uppercase board name
if [ "$BOARD_MODEL" = "pico2_w" ]; then
    BOARD_NAME="RPI_PICO2_W"
elif [ "$BOARD_MODEL" = "pico_w" ]; then
    BOARD_NAME="RPI_PICO_W"
else
    echo "❌ Unknown BOARD_MODEL: $BOARD_MODEL"
    exit 1
fi

# ─────────────────────────────────────────
# MODULES — Using the portable path function
SDK_PATH=$(get_abspath "pico-sdk")
HELLO_MODULE=$(get_abspath "modules/hello/micropython.cmake")
SQLITE_MODULE=$(get_abspath "modules/sqlite/micropython.cmake")

# Note: SDCARD_MODULE wasn't defined in your snippet, ensure it's set if needed
MODULES_PATHS="${HELLO_MODULE};${SQLITE_MODULE}"
# ─────────────────────────────────────────

# Navigate to port directory
cd micropython/ports/rp2
rm -rf build

# Run CMake
cmake -S . -B build \
    -DPICO_BOARD="$BOARD_MODEL" \
    -DBOARD="$BOARD_NAME" \
    -DMICROPY_BOARD="$BOARD_NAME" \
    -DPICO_SDK_PATH="$SDK_PATH" \
    -DUSER_C_MODULES="$MODULES_PATHS"

# Multi-platform CPU core detection
if [[ "$OSTYPE" == "darwin"* ]]; then
    JOBS=$(sysctl -n hw.ncpu)
else
    JOBS=$(nproc 2>/dev/null || echo 4)
fi

echo "🚀 Building with $JOBS jobs..."
make -j"$JOBS" -C build

# Return to root and copy firmware
cd ../../..
mkdir -p build

# Find the uf2 file (works on both BSD and GNU find)
FIRMWARE_SOURCE=$(find micropython/ports/rp2/build -name "firmware.uf2" | head -n 1)

if [ -f "$FIRMWARE_SOURCE" ]; then
    cp "$FIRMWARE_SOURCE" build/micropython_potatao.uf2
    echo "✅ Done! Firmware is at:"
    echo "   $(get_abspath build/micropython_potatao.uf2)"
else
    echo "❌ Error: firmware.uf2 not found!"
    exit 1
fi