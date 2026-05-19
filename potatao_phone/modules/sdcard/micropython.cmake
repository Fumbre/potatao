add_library(usermod_sdcard INTERFACE)

target_sources(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.c
)

target_include_directories(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod_sdcard INTERFACE
    usermod
)

target_link_libraries(usermod INTERFACE usermod_sdcard)
