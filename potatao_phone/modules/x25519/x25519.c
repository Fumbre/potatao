#include "py/runtime.h"
#include "py/obj.h"
#include "py/objstr.h"

extern void x25519(void *dst, const void *src, const void *scalar);

static mp_obj_t mod_x25519_calculate(mp_obj_t scalar_obj, mp_obj_t point_obj) {
    mp_buffer_info_t scalar_buf;
    mp_buffer_info_t point_buf;
    
    mp_get_buffer_raise(scalar_obj, &scalar_buf, MP_BUFFER_READ);
    mp_get_buffer_raise(point_obj, &point_buf, MP_BUFFER_READ);

    if (scalar_buf.len != 32 || point_buf.len != 32) {
        mp_raise_ValueError(MP_ERROR_TEXT("Inputs must be exactly 32 bytes"));
    }

    vstr_t vstr;
    vstr_init_len(&vstr, 32);

    x25519((uint8_t*)vstr.buf, point_buf.buf, scalar_buf.buf);

    return mp_obj_new_bytes_from_vstr(&vstr);
}
static MP_DEFINE_CONST_FUN_OBJ_2(mod_x25519_calculate_obj, mod_x25519_calculate);

static const MP_DEFINE_STR_OBJ(x25519_base_point_obj, "\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00");

static const mp_rom_map_elem_t mp_module_x25519_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_x25519) },
    { MP_ROM_QSTR(MP_QSTR_calculate), MP_ROM_PTR(&mod_x25519_calculate_obj) },
    { MP_ROM_QSTR(MP_QSTR_BASE_POINT), MP_ROM_PTR(&x25519_base_point_obj) },
};
static MP_DEFINE_CONST_DICT(mp_module_x25519_globals, mp_module_x25519_globals_table);

const mp_obj_module_t mp_module_x25519 = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mp_module_x25519_globals,
};

MP_REGISTER_MODULE(MP_QSTR_x25519, mp_module_x25519);