#include "audio.h"

// removed 'static' so it's accessible externally via extern in header
audio_format_t audio_format = {
    .sample_freq = 44100,
    .format = AUDIO_BUFFER_FORMAT_PCM_S16,
    .channel_count = 2
};

static audio_buffer_format_t producer_format = {
    .format = &audio_format,
    .sample_stride = 4
};

audio_buffer_pool_t* audio_init_pool() {
    return audio_new_producer_pool(&producer_format, 3, SAMPLES_PER_BUFFER);
}

void audio_fill_buffer(audio_buffer_pool_t* pool,
                       const uint8_t* data,
                       uint32_t data_len,
                       uint32_t* byte_index) {
    struct audio_buffer *buffer = take_audio_buffer(pool, true);
    int16_t *samples = (int16_t *) buffer->buffer->bytes;

    for (uint i = 0; i < buffer->max_sample_count; i++) {
        if (*byte_index + 1 < data_len) {
            int16_t sample = (int16_t)(
                (data[*byte_index + 1] << 8) | (data[*byte_index] & 0xFF)
            );
            samples[i*2]   = sample;
            samples[i*2+1] = sample;
            *byte_index += 2;
        } else {
            *byte_index = 0;
        }
    }

    buffer->sample_count = buffer->max_sample_count;
    give_audio_buffer(pool, buffer);
}