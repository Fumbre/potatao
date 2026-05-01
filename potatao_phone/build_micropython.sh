#!/bin/bash
set -e

echo "Building MicroPython for RPI_PICO2_W..."

SDK_PATH=$(realpath pico-sdk)
SDCARD_MODULE="$(realpath modules/sdcard/micropython.cmake)"
HELLO_MODULE="$(realpath modules/hello/micropython.cmake)"
MODULE_PATHS="${HELLO_MODULE};${SDCARD_MODULE}"

cd micropython/ports/rp2

rm -rf build

cmake -S . -B build \
    -DPICO_BOARD=pico_w\
    -DBOARD=RPI_PICO_W \
    -DMICROPY_BOARD=RPI_PICO_W \
    -DPICO_SDK_PATH="$SDK_PATH" \
    -DUSER_C_MODULES="$MODULE_PATHS"

make -j$(nproc) -C build

echo "Done!"
find build -name "firmware.uf2"