#include "py/runtime.h"
#include "py/obj.h"
#include "py/mperrno.h"
#include "sdcard.h"
#include <stdint.h>

// ── Object struct: holds pointer to C++ SDCard instance ─────────────────────
typedef struct _sdcard_obj_t {
    mp_obj_base_t base;
    void *sd_ptr;
} sdcard_obj_t;

// ── Constructor: SDCard(spi_id, sck, mosi, miso, cs) ────────────────────────
static mp_obj_t sdcard_make_new(const mp_obj_type_t *type,
                                 size_t n_args, size_t n_kw,
                                 const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 5, 5, false);

    int  spi_id = mp_obj_get_int(args[0]);
    uint sck    = mp_obj_get_int(args[1]);
    uint mosi   = mp_obj_get_int(args[2]);
    uint miso   = mp_obj_get_int(args[3]);
    uint cs     = mp_obj_get_int(args[4]);

    sdcard_obj_t *self = mp_obj_malloc(sdcard_obj_t, type);
    self->sd_ptr = sdcard_new(spi_id, sck, mosi, miso, cs);
    if (!self->sd_ptr) {
        mp_raise_OSError(MP_ENOMEM);
    }
    return MP_OBJ_FROM_PTR(self);
}

// ── mount() ──────────────────────────────────────────────────────────────────
static mp_obj_t sdcard_mount(mp_obj_t self_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    int ret = sdcard_disk_init(self->sd_ptr);
    if (ret != 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(sdcard_mount_obj, sdcard_mount);

// ── readblocks(sector, buf) ───────────────────────────────────────────────────
static mp_obj_t sdcard_readblocks(mp_obj_t self_in,
                                   mp_obj_t sector_in,
                                   mp_obj_t buf_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    uint32_t sector = mp_obj_get_int(sector_in);

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_WRITE);
    uint32_t count = bufinfo.len / 512;

    int ret = sdcard_disk_read(self->sd_ptr, bufinfo.buf, sector, count);
    if (ret != 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_readblocks_obj, sdcard_readblocks);

// ── writeblocks(sector, buf) ──────────────────────────────────────────────────
static mp_obj_t sdcard_writeblocks(mp_obj_t self_in,
                                    mp_obj_t sector_in,
                                    mp_obj_t buf_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    uint32_t sector = mp_obj_get_int(sector_in);

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_READ);
    uint32_t count = bufinfo.len / 512;

    int ret = sdcard_disk_write(self->sd_ptr, bufinfo.buf, sector, count);
    if (ret != 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_writeblocks_obj, sdcard_writeblocks);

// ── ioctl(op, arg) ────────────────────────────────────────────────────────────
#define IOCTL_SYNC        3
#define IOCTL_BLOCK_COUNT 4
#define IOCTL_BLOCK_SIZE  5
#define IOCTL_BLOCK_ERASE 6

static mp_obj_t sdcard_ioctl(mp_obj_t self_in,
                              mp_obj_t op_in,
                              mp_obj_t arg_in) {
    int op = mp_obj_get_int(op_in);
    switch (op) {
        case IOCTL_SYNC:        return MP_OBJ_NEW_SMALL_INT(0);
        case IOCTL_BLOCK_SIZE:  return MP_OBJ_NEW_SMALL_INT(512);
        case IOCTL_BLOCK_COUNT: return MP_OBJ_NEW_SMALL_INT(0);
        default:                return MP_OBJ_NEW_SMALL_INT(-1);
    }
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_ioctl_obj, sdcard_ioctl);

// ── __del__: release C++ object ───────────────────────────────────────────────
static mp_obj_t sdcard_del(mp_obj_t self_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    sdcard_destroy(self->sd_ptr);
    self->sd_ptr = NULL;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(sdcard_del_obj, sdcard_del);

// ── Method table ──────────────────────────────────────────────────────────────
static const mp_rom_map_elem_t sdcard_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_mount),       MP_ROM_PTR(&sdcard_mount_obj) },
    { MP_ROM_QSTR(MP_QSTR_readblocks),  MP_ROM_PTR(&sdcard_readblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_writeblocks), MP_ROM_PTR(&sdcard_writeblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_ioctl),       MP_ROM_PTR(&sdcard_ioctl_obj) },
    { MP_ROM_QSTR(MP_QSTR___del__),     MP_ROM_PTR(&sdcard_del_obj) },
};
static MP_DEFINE_CONST_DICT(sdcard_locals_dict, sdcard_locals_dict_table);

// ── Type definition (compatible with MicroPython v1.20+) ─────────────────────
MP_DEFINE_CONST_OBJ_TYPE(
    sdcard_type,
    MP_QSTR_SDCard,
    MP_TYPE_FLAG_NONE,
    make_new, sdcard_make_new,
    locals_dict, &sdcard_locals_dict
);

// ── Module registration ───────────────────────────────────────────────────────
static const mp_rom_map_elem_t sdcard_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sdcard) },
    { MP_ROM_QSTR(MP_QSTR_SDCard),   MP_ROM_PTR(&sdcard_type) },
};
static MP_DEFINE_CONST_DICT(sdcard_module_globals, sdcard_module_globals_table);

const mp_obj_module_t sdcard_user_cmodule = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&sdcard_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_sdcard, sdcard_user_cmodule);