#include "speaker.h"

void speaker_init(audio_buffer_pool_t* pool, audio_format_t* format) {
    struct audio_i2s_config config = {
        .data_pin = 4,
        .clock_pin_base = 2,
        .dma_channel = 0,
        .pio_sm = 0,
    };

    audio_i2s_setup(format, &config);
    audio_i2s_connect(pool);
    audio_i2s_set_enabled(true);
}