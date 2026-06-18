#include "py/runtime.h"
#include "py/obj.h"
#include "py/binary.h"
#include <stdint.h>

// Python: mic_dsp.convert(input_buf, output_buf, gain)
// input_buf:  bytearray of 32-bit samples from I2S
// output_buf: bytearray to write 16-bit samples into
// gain:       integer multiplier
static mp_obj_t mic_dsp_convert(mp_obj_t in_obj,
                                mp_obj_t out_obj,
                                mp_obj_t gain_obj)
{
    mp_buffer_info_t in_buf, out_buf;
    mp_get_buffer_raise(in_obj, &in_buf, MP_BUFFER_READ);
    mp_get_buffer_raise(out_obj, &out_buf, MP_BUFFER_WRITE);

    int gain = mp_obj_get_int(gain_obj);

    const uint8_t *in = (const uint8_t *)in_buf.buf;
    uint8_t *out = (uint8_t *)out_buf.buf;

    size_t num_samples = in_buf.len / 4;

    for (size_t i = 0; i < num_samples; i++)
    {
        // read 32-bit little endian sample
        int32_t s = (int32_t)((uint32_t)in[i * 4] |
                              (uint32_t)in[i * 4 + 1] << 8 |
                              (uint32_t)in[i * 4 + 2] << 16 |
                              (uint32_t)in[i * 4 + 3] << 24);

        // INMP441: data in top 24 bits
        s >>= 16;

        // apply gain
        s *= gain;

        // clamp to 16-bit
        if (s > 32767)
            s = 32767;
        if (s < -32768)
            s = -32768;

        // write 16-bit little endian
        out[i * 2] = (uint8_t)(s & 0xFF);
        out[i * 2 + 1] = (uint8_t)((s >> 8) & 0xFF);
    }

    return mp_obj_new_int(num_samples * 2); // bytes written
}
static MP_DEFINE_CONST_FUN_OBJ_3(mic_dsp_convert_obj, mic_dsp_convert);

static const mp_rom_map_elem_t mic_dsp_module_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_mic_dsp)},
    {MP_ROM_QSTR(MP_QSTR_convert), MP_OBJ_FROM_PTR(&mic_dsp_convert_obj)},
};

static MP_DEFINE_CONST_DICT(mic_dsp_module_globals, mic_dsp_module_globals_table);

const mp_obj_module_t mic_dsp_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&mic_dsp_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_mic_dsp, mic_dsp_module);
