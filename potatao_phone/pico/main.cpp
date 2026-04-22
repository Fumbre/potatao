#include "pico/stdlib.h"
#include "audio/audio.h"
#include "speaker/speaker.h"
#include "dogbark_data.h"

int main() {
    stdio_init_all();

    audio_buffer_pool_t* pool = audio_init_pool();
    speaker_init(pool, &audio_format);

    uint32_t byte_index = 0;
    while (true) {
        audio_fill_buffer(pool, dogbark_raw, dogbark_raw_len, &byte_index);
    }
}