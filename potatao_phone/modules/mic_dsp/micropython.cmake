add_library(usermod_mic_dsp INTERFACE)

target_sources(usermod_mic_dsp INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/mic_dsp.c
)

target_include_directories(usermod_mic_dsp INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod_mic_dsp INTERFACE usermod)
target_link_libraries(usermod INTERFACE usermod_mic_dsp)