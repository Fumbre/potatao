#pragma once
#include "pico/audio_i2s.h"

#define SAMPLES_PER_BUFFER 256

// exposed so speaker can use it
extern audio_format_t audio_format;

audio_buffer_pool_t* audio_init_pool();
void audio_fill_buffer(audio_buffer_pool_t* pool,
                       const uint8_t* data,
                       uint32_t data_len,
                       uint32_t* byte_index);