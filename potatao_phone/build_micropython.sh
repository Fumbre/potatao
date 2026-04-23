#!/bin/bash
set -e

echo "Building MicroPython for RPI_PICO2_W..."

SDK_PATH=$(realpath pico-sdk)
# MODULE_PATHS="$(realpath modules/audio/micropython.cmake);$(realpath modules/speaker/micropython.cmake)"

cd micropython/ports/rp2

rm -rf build  # clean build needed after cmake changes

cmake -S . -B build \
    -DPICO_BOARD=pico2_w \
    -DBOARD=RPI_PICO2_W \
    -DMICROPY_BOARD=RPI_PICO2_W \
    -DPICO_SDK_PATH="$SDK_PATH" \
    # -DUSER_C_MODULES="$MODULE_PATHS"

make -j$(nproc) -C build

echo "Done! Your .uf2 is at:"
find build -name "firmware.uf2"