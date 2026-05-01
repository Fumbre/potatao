add_library(usermod_sdcard INTERFACE)

# source files
target_sources(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.c
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.cpp
)

# include path
target_include_directories(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)


# required libraries
target_link_libraries(usermod_sdcard INTERFACE
    usermod
    pico_stdlib
    hardware_spi
    hardware_gpio
)

# C++17
target_compile_features(usermod_sdcard INTERFACE cxx_std_17)

# VERY IMPORTANT !!!
# without this, module won't enter final firmware
target_link_libraries(usermod INTERFACE usermod_sdcard)