#!/bin/bash
set -e

# ─────────────────────────────────────────
# CONFIGURATION — change this to switch boards
# Options:
#   pico_w   → RPI_PICO_W
#   pico2_w  → RPI_PICO2_W
BOARD_MODEL="pico2_w"
# ─────────────────────────────────────────


# Auto-set the uppercase board name from BOARD_MODEL
if [ "$BOARD_MODEL" = "pico2_w" ]; then
    BOARD_NAME="RPI_PICO2_W"
elif [ "$BOARD_MODEL" = "pico_w" ]; then
    BOARD_NAME="RPI_PICO_W"
else
    echo "❌ Unknown BOARD_MODEL: $BOARD_MODEL"
    echo "   Valid options: pico_w, pico2_w"
    exit 1
fi


# ─────────────────────────────────────────
# MODULES — add your own custom module to micropython build
SDK_PATH=$(realpath pico-sdk)
SDCARD_MODULE="$(realpath modules/sdcard/micropython.cmake)"
HELLO_MODULE="$(realpath modules/hello/micropython.cmake)"
SQLITE_MODULE="$(realpath modules/sqlite/micropython.cmake)"

MODULES_PATHS="${HELLO_MODULE};${SDCARD_MODULE};${SQLITE_MODULE}"
# ─────────────────────────────────────────

# Remove previous build
cd micropython/ports/rp2
rm -rf build

cmake -S . -B build \
    -DPICO_BOARD="$BOARD_MODEL" \
    -DBOARD="$BOARD_NAME" \
    -DMICROPY_BOARD="$BOARD_NAME" \
    -DPICO_SDK_PATH="$SDK_PATH" \
    -DUSER_C_MODULES="$MODULES_PATHS"

make -j$(nproc) -C build

# Copy firmware to project root build folder
cd ../../..
mkdir -p build
cp $(find micropython/ports/rp2/build -name "firmware.uf2") build/micropython_potatao.uf2

echo "✅ Done! Firmware is at:"
echo "   $(realpath build/micropython_potatao.uf2)"