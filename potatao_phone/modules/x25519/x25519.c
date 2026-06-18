#include "py/runtime.h"
#include "py/obj.h"
#include "py/objstr.h"
#include "py/binary.h"
#include <string.h>

extern void x25519(void *dst, const void *src, const void *scalar);

#define TRNG_BASE_ADDR 0x400cc000
#define TRNG_CTRL_REG  (*(volatile uint32_t *)(TRNG_BASE_ADDR + 0x00))
#define TRNG_DATA_REG  (*(volatile uint32_t *)(TRNG_BASE_ADDR + 0x08))

static uint32_t get_random_u32(void) {
    while (!(TRNG_CTRL_REG & 1)) {
        // Wait for hardware entropy to be ready
    }
    return TRNG_DATA_REG;
}

static mp_obj_t mod_x25519_calculate(mp_obj_t scalar_obj, mp_obj_t point_obj) {
    mp_buffer_info_t scalar_buf, point_buf;
    mp_get_buffer_raise(scalar_obj, &scalar_buf, MP_BUFFER_READ);
    mp_get_buffer_raise(point_obj, &point_buf, MP_BUFFER_READ);

    if (scalar_buf.len != 32 || point_buf.len != 32) {
        mp_raise_ValueError(MP_ERROR_TEXT("Inputs must be 32 bytes"));
    }

    uint8_t *res = m_malloc(32);
    x25519(res, point_buf.buf, scalar_buf.buf);
    
    return mp_obj_new_bytes(res, 32);
}
static MP_DEFINE_CONST_FUN_OBJ_2(mod_x25519_calculate_obj, mod_x25519_calculate);

static mp_obj_t mod_x25519_generate_keypair(void) {
    uint8_t priv[32];
    uint8_t pub[32];
    const uint8_t base_point[32] = {9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

    for (int i = 0; i < 8; i++) {
        uint32_t val = get_random_u32();
        memcpy(&priv[i * 4], &val, 4);
    }

    // X25519 clamping
    priv[0] &= 248;
    priv[31] &= 127;
    priv[31] |= 64;

    x25519(pub, base_point, priv);

    mp_obj_t tuple[2];
    tuple[0] = mp_obj_new_bytes(priv, 32);
    tuple[1] = mp_obj_new_bytes(pub, 32);
    return mp_obj_new_tuple(2, tuple);
}
static MP_DEFINE_CONST_FUN_OBJ_0(mod_x25519_generate_keypair_obj, mod_x25519_generate_keypair);

static const MP_DEFINE_STR_OBJ(x25519_base_point_obj, "\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00");

static const mp_rom_map_elem_t mp_module_x25519_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_x25519) },
    { MP_ROM_QSTR(MP_QSTR_calculate), MP_ROM_PTR(&mod_x25519_calculate_obj) },
    { MP_ROM_QSTR(MP_QSTR_generate_keypair), MP_ROM_PTR(&mod_x25519_generate_keypair_obj) },
    { MP_ROM_QSTR(MP_QSTR_BASE_POINT), MP_ROM_PTR(&x25519_base_point_obj) },
};
static MP_DEFINE_CONST_DICT(mp_module_x25519_globals, mp_module_x25519_globals_table);

const mp_obj_module_t mp_module_x25519 = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mp_module_x25519_globals,
};

MP_REGISTER_MODULE(MP_QSTR_x25519, mp_module_x25519);