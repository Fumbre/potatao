add_library(speaker
    speaker.cpp
)

target_include_directories(speaker PUBLIC
    .   # exposes this folder so others can #include "speaker/speaker.h"
)

target_link_libraries(speaker
    audio            # speaker needs audio (uses audio_buffer_pool_t)
    pico_audio_i2s   # needs I2S hardware
    hardware_pio
    hardware_dma
)