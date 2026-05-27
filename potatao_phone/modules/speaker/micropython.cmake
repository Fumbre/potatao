# Define the Speaker module interface
add_library(usermod_speaker INTERFACE)

# Target the source file
target_sources(usermod_speaker INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/speaker.c
)

# 🌟 1. Force the PIO generator to execute early
add_dependencies(usermod_speaker pico_audio_i2s_pio_h)

# Link hardware libraries
target_link_libraries(usermod_speaker INTERFACE 
    pico_audio_i2s
    hardware_pio
)

# Connect back into the core user module assembly pipelines
target_link_libraries(usermod INTERFACE usermod_speaker)

# 🌟 2. THE CRITICAL FIX FOR MICROPYTHON'S SCANNER:
# Tell the global MicroPython core modules that they cannot run their QSTR preprocessor 
# until the pico-extras library target completely finishes generating audio_i2s.pio.h
if(TARGET MICROPY_TARGET)
    add_dependencies(MICROPY_TARGET pico_audio_i2s_pio_h)
endif()

if(TARGET BUILD_FROZEN_CONTENT)
    add_dependencies(BUILD_FROZEN_CONTENT pico_audio_i2s_pio_h)
endif()