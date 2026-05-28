#include <stdio.h>
#include "py/runtime.h"
#include "py/obj.h"
#include "py/stream.h"
#include "extmod/vfs.h"

// Protect SDK headers from MicroPython's QSTR preprocessor scanner
#ifndef NO_QSTR
#include "pico/stdlib.h"
#include "pico/util/buffer.h"
#include "pico/types.h"
#include "pico/audio_i2s.h"
#include "hardware/dma.h"
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

    mp_arg_val_t parsed_vals[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, parsed_vals);

    // Approach B: file_obj is our live open track stream passed from Python
    mp_obj_t file_obj = parsed_vals[ARG_file].u_obj;
    uint32_t sample_rate = parsed_vals[ARG_rate].u_int;
    size_t buffer_size = parsed_vals[ARG_ibuf].u_int;

    if (buffer_size == 0)
    {
        buffer_size = 1024;
    }

    // Configure for Stereo (2 channels) to feed both slots of the MAX98357A DAC/Amp
    audio_format_t audio_format = {
        .sample_freq = sample_rate,
        .format = AUDIO_BUFFER_FORMAT_PCM_S16,
        .channel_count = 2};

    audio_i2s_config_t config = {
        .data_pin = FIXED_DOUT_PIN,
        .clock_pin_base = FIXED_BCLK_PIN,
        .pio_sm = 0,
        .dma_channel = 0};

    // Safely claim a free DMA channel dynamically
    int free_dma = dma_claim_unused_channel(false);
    if (free_dma >= 0)
    {
        config.dma_channel = free_dma;
    }

    const audio_format_t *actual_format = audio_i2s_setup(&audio_format, &config);

    // Allocate buffer pool structure with safety room for stereo samples (512)
    audio_buffer_pool_t *audio_pool = audio_new_producer_pool((audio_buffer_format_t *)actual_format, 4, 512);

    audio_i2s_connect(audio_pool);
    audio_i2s_set_enabled(true);

    // Extract stream interface bindings directly from the incoming Python object
    const mp_stream_p_t *stream = mp_get_stream_raise(file_obj, MP_STREAM_OP_READ);

    uint8_t *buf = m_new(uint8_t, buffer_size);
    int errcode;

    // Skip standard WAV metadata header fields (44 bytes) to start raw PCM ingestion
    stream->ioctl(file_obj, MP_STREAM_SEEK, 44, &errcode);

    // Main DMA / I2S Transfer loop
    while (true)
    {
        // 1. Get a hardware tracking buffer structure. Blocking set to true
        // because the background I2S engine is actively draining data.
        audio_buffer_t *buffer = take_audio_buffer(audio_pool, true);

        // 2. Read raw binary chunks from the custom C SD Card module via the VFS layer
        mp_uint_t bytes_read = stream->read(file_obj, buf, buffer_size, &errcode);
        if (bytes_read == 0 || bytes_read == (mp_uint_t)-1)
        {
            // End of file or error, hand back the unused structure and exit loop
            give_audio_buffer(audio_pool, buffer);
            break;
        }

        int mono_samples = bytes_read / sizeof(int16_t);
        int16_t *samples = (int16_t *)buffer->buffer->bytes;
        int16_t *source = (int16_t *)buf;

        // 3. Mirror the mono samples into both Left & Right slots for the MAX98357A
        int dest_index = 0;
        for (int i = 0; i < mono_samples; i++)
        {
            samples[dest_index++] = source[i]; // Left
            samples[dest_index++] = source[i]; // Right
        }

        buffer->sample_count = mono_samples * 2;

        // Push the loaded buffer directly down into the hardware background DMA engine
        give_audio_buffer(audio_pool, buffer);
    }

    // Clean up local heap tracking allocations and reset state
    m_del(uint8_t, buf, buffer_size);

    // Disable I2S clock lines to stop current flow to the amplifier
    audio_i2s_set_enabled(false);

    // Note: We DO NOT call mp_stream_close(file_obj) here,
    // because Python's "with open" block handles closing it cleanly!

    return mp_const_none;
}

static MP_DEFINE_CONST_FUN_OBJ_KW(speaker_play_obj, 1, speaker_play);

static const mp_rom_map_elem_t speaker_module_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_speaker)},
    {MP_ROM_QSTR(MP_QSTR_play), MP_ROM_PTR(&speaker_play_obj)},
};
static MP_DEFINE_CONST_DICT(speaker_module_globals, speaker_module_globals_table);

const mp_obj_module_t speaker_user_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&speaker_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_speaker, speaker_user_module);