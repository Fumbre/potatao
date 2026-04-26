add_library(usermod_sdcard INTERFACE)

target_sources(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.c
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.cpp
)

target_include_directories(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod_sdcard INTERFACE
    hardware_spi
    hardware_gpio
    pico_stdlib
    stdc++
    usermod
)