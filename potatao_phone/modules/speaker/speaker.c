#include <stdio.h>
#include "py/runtime.h"
#include "py/obj.h"
#include "py/stream.h"
#include "extmod/vfs.h"

// Protect SDK headers from MicroPython's QSTR preprocessor scanner
#ifndef NO_QSTR
#include "pico/stdlib.h"
#include "pico/util/buffer.h"
#include "pico/base_types.h"
#include "pico/audio_i2s.h"
#endif

// Fixed physical I2S pin designations for your phone board layout
#define FIXED_BCLK_PIN 2
#define FIXED_DOUT_PIN 4

static mp_obj_t speaker_play(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args)
{
    enum
    {
        ARG_file,
        ARG_rate,
        ARG_ibuf
    };
    static const mp_arg_t allowed_args[] = {
        {MP_QSTR_file, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE}},
        {MP_QSTR_rate, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 24000}}, // Default 24000 Hz
        {MP_QSTR_ibuf, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 1024}},  // Default 1024 byte buffer
    };

    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_obj_t filename_obj = args[ARG_file].u_obj;
    uint32_t sample_rate = args[ARG_rate].u_int;
    size_t buffer_size = args[ARG_ibuf].u_int;

    if (buffer_size == 0)
    {
        buffer_size = 1024;
    }

    // Configure the pico-extras audio hardware pipeline structures
    audio_format_t audio_format = {
        .sample_freq = sample_rate,
        .format = AUDIO_BUFFER_FORMAT_PCM_S16,
        .channel_count = 1};

    audio_i2s_config_t config = {
        .data_pin = FIXED_DOUT_PIN,
        .clock_pin_base = FIXED_BCLK_PIN, // BCLK and WS follow sequentially
        .pio_sm = 0,
        .dma_channel = 0};

    // Open physical connection allocations
    audio_buffer_pool_t *audio_pool = audio_i2s_setup(&audio_format, &config);
    audio_i2s_connect(audio_pool);
    audio_i2s_set_enabled(true);

    // Open file securely using the internal MicroPython VFS layer (handles /sd paths automatically)
    mp_obj_t open_args[2] = {filename_obj, MP_OBJ_NEW_QSTR(MP_QSTR_rb)};
    mp_obj_t file_obj = mp_vfs_open(MP_ARRAY_SIZE(open_args), open_args, (mp_map_t *)&mp_const_empty_map);

    if (file_obj == MP_OBJ_NULL)
    {
        audio_i2s_set_enabled(false);
        mp_raise_ValueError(MP_ERROR_TEXT("Failed to open audio track file"));
    }

    const mp_stream_p_t *stream = mp_get_stream_raise(file_obj, MP_STREAM_READ);

    uint8_t *buf = m_new(uint8_t, buffer_size);
    int errcode;

    // Skip standard WAV metadata header fields (44 bytes) to start raw PCM ingestion
    stream->ioctl(file_obj, MP_STREAM_SEEK, 44, &errcode);

    // Main DMA / I2S Transfer loop
    while (true)
    {
        mp_uint_t bytes_read = stream->read(file_obj, buf, buffer_size, &errcode);
        if (bytes_read == 0 || bytes_read == (mp_uint_t)-1)
        {
            break;
        }

        // Pull an empty target structure from the C audio queue
        audio_buffer_t *buffer = take_audio_buffer(audio_pool, true);

        int samples_count = bytes_read / 2;
        int16_t *samples = (int16_t *)buffer->buffer->bytes;
        int16_t *source = (int16_t *)buf;

        // Perform fast data assignment migration
        for (int i = 0; i < samples_count; i++)
        {
            samples[i] = source[i];
        }

        buffer->sample_count = samples_count;

        // Pass the loaded buffer back into the hardware background DMA pipeline
        give_audio_buffer(audio_pool, buffer);
    }

    // Clean up heap tracking allocations and reset state
    m_del(uint8_t, buf, buffer_size);
    mp_stream_close(file_obj);
    audio_i2s_set_enabled(false);

    return mp_const_none;
}

// Map the signature keyword properties
static MP_DEFINE_CONST_FUN_OBJ_KW(speaker_play_obj, 1, speaker_play);

// Build the global table interface maps exposing names to Python
static const mp_rom_map_elem_t speaker_module_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_speaker)},
    {MP_ROM_QSTR(MP_QSTR_play), MP_ROM_PTR(&speaker_play_obj)},
};
static MP_DEFINE_CONST_DICT(speaker_module_globals, speaker_module_globals_table);

const mp_obj_module_t speaker_user_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&speaker_module_globals,
};

// Register directly to the MicroPython system framework as 'speaker'
MP_REGISTER_MODULE(MP_QSTR_speaker, speaker_user_module);