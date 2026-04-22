add_library(audio
    audio.cpp
)

target_include_directories(audio PUBLIC
    .   # exposes this folder so others can #include "audio/audio.h"
)

target_link_libraries(audio
    pico_audio_i2s   # needs this for audio_buffer_pool_t and friends
)