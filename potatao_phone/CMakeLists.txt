cmake_minimum_required(VERSION 3.13)

# ccache
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
endif()

# Board type BEFORE sdk include
set(PICO_BOARD pico2_w)

# SDK + Extras paths
set(PICO_SDK_PATH "../pico-sdk/")
set(PICO_EXTRAS_PATH "../pico-extras/")

include(pico_sdk_import.cmake)
include(pico_extras_import.cmake)

project(potatao)
pico_sdk_init()

# Tell CMake about all subfolders
add_subdirectory(lib/audio)
add_subdirectory(modules/speaker)
add_subdirectory(pico)