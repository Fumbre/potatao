#include <stdio.h>
#include "py/runtime.h"
#include "py/obj.h"
#include "py/stream.h"
#include "extmod/vfs.h"

// Чистые пути, защищенные от препроцессора MicroPython
#ifndef NO_QSTR
  #include "pico/stdlib.h"
  #include "pico/util/buffer.h"
  #include "pico/base_types.h"
  #include "pico/audio_i2s.h"
#endif

// Фиксированные пины
#define FIXED_BCLK_PIN 2
#define FIXED_DOUT_PIN 4


static mp_obj_t dogbark_play(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_file, ARG_rate, ARG_ibuf };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_file, MP_ARG_REQUIRED | MP_ARG_OBJ,  {.u_rom_obj = MP_ROM_NONE} },
        { MP_QSTR_rate, MP_ARG_KW_ONLY  | MP_ARG_INT,  {.u_int = 24000} }, // defualt 24000 Hz
        { MP_QSTR_ibuf, MP_ARG_KW_ONLY  | MP_ARG_INT,  {.u_int = 1024} },  // defualt 1024 byte
    };

    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_obj_t filename_obj = args[ARG_file].u_obj;
    uint32_t sample_rate  = args[ARG_rate].u_int;
    size_t buffer_size    = args[ARG_ibuf].u_int;

    if (buffer_size == 0) {
        buffer_size = 1024;
    }

    audio_format_t audio_format = {
        .sample_freq = sample_rate,
        .format = AUDIO_BUFFER_FORMAT_PCM_S16,
        .channel_count = 1 
    };

    audio_i2s_config_t config = {
        .data_pin = FIXED_DOUT_PIN,
        .clock_pin_base = FIXED_BCLK_PIN, // WS 
        .pio_sm = 0,
        .dma_channel = 0
    };

    audio_buffer_pool_t *audio_pool = audio_i2s_setup(&audio_format, &config);
    audio_i2s_connect(audio_pool);
    audio_i2s_set_enabled(true);

    // Open file using VFS MicroPython
    mp_obj_t open_args[2] = { filename_obj, MP_OBJ_NEW_QSTR(MP_QSTR_rb) };
    mp_obj_t file_obj = mp_vfs_open(MP_ARRAY_SIZE(open_args), open_args, (mp_map_t *)&mp_const_empty_map);
    
    if (file_obj == MP_OBJ_NULL) {
        audio_i2s_set_enabled(false);
        mp_raise_ValueError(MP_ERROR_TEXT("Failed to open file"));
    }

    const mp_stream_p_t *stream = mp_get_stream_raise(file_obj, MP_STREAM_READ);

    uint8_t *buf = m_new(uint8_t, buffer_size);
    int errcode;

    // skip the standart WAV header (44 byte)
    stream->ioctl(file_obj, MP_STREAM_SEEK, 44, &errcode);

    // 4. sending DMA/I2S
    while (true) {
        mp_uint_t bytes_read = stream->read(file_obj, buf, buffer_size, &errcode);
        if (bytes_read == 0 || bytes_read == (mp_uint_t)-1) {
            break;
        }

        audio_buffer_t *buffer = take_audio_buffer(audio_pool, true);
        
        int samples_count = bytes_read / 2;
        int16_t *samples = (int16_t *)buffer->buffer->bytes;
        int16_t *source = (int16_t *)buf;

        for (int i = 0; i < samples_count; i++) {
            samples[i] = source[i];
        }

        buffer->sample_count = samples_count;
        give_audio_buffer(audio_pool, buffer);
    }

    // 5. clear memory close a file
    m_del(uint8_t, buf, buffer_size);
    mp_stream_close(file_obj);
    audio_i2s_set_enabled(false);

    return mp_const_none;
}

// register function
static MP_DEFINE_CONST_FUN_OBJ_KW(dogbark_play_obj, 1, dogbark_play);

static const mp_rom_map_elem_t dogbark_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_dogbark) },
    { MP_ROM_QSTR(MP_QSTR_play),     MP_ROM_PTR(&dogbark_play_obj) },
};
static MP_DEFINE_CONST_DICT(dogbark_module_globals, dogbark_module_globals_table);

const mp_obj_module_t dogbark_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&dogbark_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_dogbark, dogbark_user_module);