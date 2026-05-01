#include "py/runtime.h"
#include "py/obj.h"
#include "py/mperrno.h"
#include "sdcard.h"

typedef struct _sdcard_obj_t {
    mp_obj_base_t base;
    void *sd_ptr;
} sdcard_obj_t;

static mp_obj_t sdcard_make_new(const mp_obj_type_t *type,
    size_t n_args, size_t n_kw, const mp_obj_t *args) {

    mp_arg_check_num(n_args, n_kw, 5, 5, false);

    sdcard_obj_t *self = mp_obj_malloc(sdcard_obj_t, type);

    self->sd_ptr = sdcard_new(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4])
    );

    if (!self->sd_ptr) {
        mp_raise_OSError(MP_ENOMEM);
    }

    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t sdcard_mount(mp_obj_t self_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (sdcard_disk_init(self->sd_ptr) != 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(sdcard_mount_obj, sdcard_mount);

static mp_obj_t sdcard_readblocks(mp_obj_t self_in, mp_obj_t sector_in, mp_obj_t buf_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_WRITE);

    if (sdcard_disk_read(self->sd_ptr,
        bufinfo.buf,
        mp_obj_get_int(sector_in),
        bufinfo.len / 512) != 0) {
        mp_raise_OSError(MP_EIO);
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_readblocks_obj, sdcard_readblocks);

static mp_obj_t sdcard_writeblocks(mp_obj_t self_in, mp_obj_t sector_in, mp_obj_t buf_in) {
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_READ);

    if (sdcard_disk_write(self->sd_ptr,
        bufinfo.buf,
        mp_obj_get_int(sector_in),
        bufinfo.len / 512) != 0) {
        mp_raise_OSError(MP_EIO);
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_writeblocks_obj, sdcard_writeblocks);

static mp_obj_t sdcard_ioctl(mp_obj_t self_in, mp_obj_t op_in, mp_obj_t arg_in) {
    int ret = sdcard_disk_ioctl(
        ((sdcard_obj_t*)MP_OBJ_TO_PTR(self_in))->sd_ptr,
        mp_obj_get_int(op_in),
        mp_obj_get_int(arg_in)
    );
    return MP_OBJ_NEW_SMALL_INT(ret);
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_ioctl_obj, sdcard_ioctl);

static const mp_rom_map_elem_t sdcard_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_mount), MP_ROM_PTR(&sdcard_mount_obj) },
    { MP_ROM_QSTR(MP_QSTR_readblocks), MP_ROM_PTR(&sdcard_readblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_writeblocks), MP_ROM_PTR(&sdcard_writeblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_ioctl), MP_ROM_PTR(&sdcard_ioctl_obj) },
};

static MP_DEFINE_CONST_DICT(sdcard_locals_dict, sdcard_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    sdcard_type,
    MP_QSTR_SDCard,
    MP_TYPE_FLAG_NONE,
    make_new, sdcard_make_new,
    locals_dict, &sdcard_locals_dict
);

static const mp_rom_map_elem_t sdcard_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sdcard) },
    { MP_ROM_QSTR(MP_QSTR_SDCard), MP_ROM_PTR(&sdcard_type) },
};

static MP_DEFINE_CONST_DICT(sdcard_module_globals, sdcard_module_globals_table);

const mp_obj_module_t sdcard_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&sdcard_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_sdcard, sdcard_user_cmodule);