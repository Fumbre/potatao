#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

abs_path() {
    local path="$1"
    local dir
    local base

    dir="$(cd "$(dirname "$path")" && pwd -P)"
    base="$(basename "$path")"
    printf '%s/%s\n' "$dir" "$base"
}

cpu_count() {
    if command -v nproc >/dev/null 2>&1; then
        nproc
    elif command -v getconf >/dev/null 2>&1; then
        getconf _NPROCESSORS_ONLN
    elif command -v sysctl >/dev/null 2>&1; then
        sysctl -n hw.ncpu 2>/dev/null || printf '1\n'
    else
        printf '1\n'
    fi
}

toolchain_has_runtime() {
    local gcc="$1"
    local file
    local resolved

    for file in nosys.specs libc.a libnosys.a; do
        resolved="$("$gcc" -print-file-name="$file" 2>/dev/null || true)"
        [ "$resolved" != "$file" ] && [ -f "$resolved" ] || return 1
    done
}

select_arm_toolchain() {
    local gcc

    if command -v arm-none-eabi-gcc >/dev/null 2>&1; then
        gcc="$(command -v arm-none-eabi-gcc)"
        if toolchain_has_runtime "$gcc"; then
            return
        fi
    fi

    for gcc in \
        "$SCRIPT_DIR"/../.toolchains/*/bin/arm-none-eabi-gcc \
        /Applications/ArmGNUToolchain/*/arm-none-eabi/bin/arm-none-eabi-gcc; do
        [ -x "$gcc" ] || continue
        if toolchain_has_runtime "$gcc"; then
            export PATH="$(dirname "$gcc"):$PATH"
            return
        fi
    done

    echo "❌ arm-none-eabi-gcc is missing the embedded C runtime."
    echo "   On macOS, install the Arm GNU toolchain:"
    echo "   brew install --cask gcc-arm-embedded"
    echo "   Then rerun this script."
    exit 1
}

choose_output_dir() {
    local preferred="$SCRIPT_DIR/build"
    local fallback="$SCRIPT_DIR/.build"

    if mkdir -p "$preferred" 2>/dev/null && [ -w "$preferred" ]; then
        printf '%s\n' "$preferred"
    else
        echo "⚠️  $preferred is not writable; using $fallback instead." >&2
        mkdir -p "$fallback"
        printf '%s\n' "$fallback"
    fi
}

BOARD_MODEL="${BOARD_MODEL:-pico2_w}"
BUILD_TYPE="${1:-Release}"

if [ "$BOARD_MODEL" = "pico2_w" ]; then
    BOARD_NAME="RPI_PICO2_W"
elif [ "$BOARD_MODEL" = "pico_w" ]; then
    BOARD_NAME="RPI_PICO_W"
else
    echo "❌ Unknown BOARD_MODEL: $BOARD_MODEL"
    echo "   Valid options: pico_w, pico2_w"
    exit 1
fi

SDK_PATH="$(abs_path "$SCRIPT_DIR/pico-sdk")"
PICO_EXTRAS_PATH="$(abs_path "$SCRIPT_DIR/pico-extras")"
HELLO_MODULE="$(abs_path "$SCRIPT_DIR/modules/hello/micropython.cmake")"
SQLITE_MODULE="$(abs_path "$SCRIPT_DIR/modules/sqlite/micropython.cmake")"
SDCARD_MODULE="$(abs_path "$SCRIPT_DIR/modules/sdcard/micropython.cmake")"
MIC_DSP_MODULE="$(abs_path "$SCRIPT_DIR/modules/mic_dsp/micropython.cmake")"
# SPEAKER_MODULE="$(abs_path "$SCRIPT_DIR/modules/speaker/micropython.cmake")"
X25519_MODULE="$(abs_path "$SCRIPT_DIR/modules/x25519/micropython.cmake")"
JWT_MODULE="$(abs_path "$SCRIPT_DIR/modules/jwt/micropython.cmake")"    

# MODULES_PATHS="${HELLO_MODULE};${SQLITE_MODULE};${SDCARD_MODULE};${MIC_DSP_MODULE};${SPEAKER_MODULE}${X25519_MODULE};${JWT_MODULE};"
MODULES_PATHS="${HELLO_MODULE};${SQLITE_MODULE};${SDCARD_MODULE};${MIC_DSP_MODULE};${SPEAKER_MODULE};"

RP2_DIR="$SCRIPT_DIR/micropython/ports/rp2"
OUTPUT_DIR="$(choose_output_dir)"
BUILD_DIR="$OUTPUT_DIR/micropython-rp2-$BOARD_MODEL"
OUTPUT_UF2="$OUTPUT_DIR/micropython_potatao.uf2"

select_arm_toolchain

rm -rf "$BUILD_DIR"

export CFLAGS="-Wno-stringop-overflow -Wno-stringop-overread -Wno-maybe-uninitialized"
export CXXFLAGS="-Wno-stringop-overflow -Wno-stringop-overread -Wno-maybe-uninitialized"

cmake -S "$RP2_DIR" -B "$BUILD_DIR" \
    -DPICO_BOARD="$BOARD_MODEL" \
    -DPICO_PLATFORM=rp2350 \
    -DBOARD="$BOARD_NAME" \
    -DMICROPY_BOARD="$BOARD_NAME" \
    -DPICO_SDK_PATH="$SDK_PATH" \
    -DUSER_C_MODULES="$MODULES_PATHS" \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
#   -DPICO_SDK_POST_LIST_DIRS="${PICO_EXTRAS_PATH}" \
cmake --build "$BUILD_DIR" --parallel "$(cpu_count)"

cp "$BUILD_DIR/firmware.uf2" "$OUTPUT_UF2"

echo "✅ Done! Firmware is at:"
echo "   $OUTPUT_UF2"