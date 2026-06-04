#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "py/mperrno.h"
#include "py/mphal.h"
#include "py/obj.h"
#include "py/objstr.h"
#include "py/runtime.h"
#include "extmod/vfs.h"

#define SDCARD_CMD_TIMEOUT (100)
#define SDCARD_WRITE_TIMEOUT_MS (1000)
#define SDCARD_BLOCK_SIZE (512)

#define SDCARD_R1_IDLE_STATE (1 << 0)
#define SDCARD_R1_ILLEGAL_COMMAND (1 << 2)

#define SDCARD_TOKEN_CMD25 (0xfc)
#define SDCARD_TOKEN_STOP_TRAN (0xfd)
#define SDCARD_TOKEN_DATA (0xfe)

typedef struct _sdcard_obj_t
{
    mp_obj_base_t base;
    mp_obj_t spi;
    mp_obj_t cs;
    uint32_t sectors;
    uint32_t cdv;
    uint8_t cmdbuf[6];
    uint8_t dummybuf[SDCARD_BLOCK_SIZE];
    uint8_t tokenbuf[1];
} sdcard_obj_t;

extern const mp_obj_type_t sdcard_type;

static const uint8_t sdcard_ff_data[] = {0xff};
static MP_DEFINE_BYTES_OBJ(sdcard_ff_obj, sdcard_ff_data, sizeof(sdcard_ff_data));

static uint8_t sdcard_crc7(const uint8_t *buf, size_t len)
{
    uint8_t crc = 0;
    for (size_t i = 0; i < len; ++i)
    {
        crc ^= buf[i];
        for (size_t j = 0; j < 8; ++j)
        {
            crc = ((crc << 1) ^ (0x12 * (crc >> 7))) & 0xff;
        }
    }
    return crc;
}

static void sdcard_spi_write_obj(sdcard_obj_t *self, mp_obj_t buf)
{
    mp_obj_t args[3];
    mp_load_method(self->spi, MP_QSTR_write, args);
    args[2] = buf;
    mp_call_method_n_kw(1, 0, args);
}

static void sdcard_spi_write_buf(sdcard_obj_t *self, const uint8_t *buf, size_t len)
{
    sdcard_spi_write_obj(self, mp_obj_new_bytearray_by_ref(len, (void *)buf));
}

static void sdcard_spi_write_ff(sdcard_obj_t *self)
{
    sdcard_spi_write_obj(self, MP_OBJ_FROM_PTR(&sdcard_ff_obj));
}

static void sdcard_spi_readinto(sdcard_obj_t *self, uint8_t *buf, size_t len, uint8_t fill)
{
    mp_obj_t args[4];
    mp_load_method(self->spi, MP_QSTR_readinto, args);
    args[2] = mp_obj_new_bytearray_by_ref(len, buf);
    args[3] = MP_OBJ_NEW_SMALL_INT(fill);
    mp_call_method_n_kw(2, 0, args);
}

static void sdcard_spi_write_readinto(sdcard_obj_t *self, const uint8_t *out_buf, uint8_t *in_buf, size_t len)
{
    mp_obj_t args[4];
    mp_load_method(self->spi, MP_QSTR_write_readinto, args);
    args[2] = mp_obj_new_bytearray_by_ref(len, (void *)out_buf);
    args[3] = mp_obj_new_bytearray_by_ref(len, in_buf);
    mp_call_method_n_kw(2, 0, args);
}

static void sdcard_cs_set(sdcard_obj_t *self, int value)
{
    mp_call_function_1(self->cs, MP_OBJ_NEW_SMALL_INT(value));
}

static void sdcard_cs_init(sdcard_obj_t *self)
{
    mp_obj_t args[5];
    mp_load_method(self->cs, MP_QSTR_init, args);
    args[2] = mp_load_attr(self->cs, MP_QSTR_OUT);
    args[3] = MP_OBJ_NEW_QSTR(MP_QSTR_value);
    args[4] = MP_OBJ_NEW_SMALL_INT(1);
    mp_call_method_n_kw(1, 1, args);
}

static void sdcard_spi_init(sdcard_obj_t *self, uint32_t baudrate)
{
    mp_obj_t args[8];
    mp_load_method(self->spi, MP_QSTR_init, args);
    args[2] = MP_OBJ_NEW_QSTR(MP_QSTR_baudrate);
    args[3] = mp_obj_new_int_from_uint(baudrate);
    args[4] = MP_OBJ_NEW_QSTR(MP_QSTR_polarity);
    args[5] = MP_OBJ_NEW_SMALL_INT(0);
    args[6] = MP_OBJ_NEW_QSTR(MP_QSTR_phase);
    args[7] = MP_OBJ_NEW_SMALL_INT(0);
    mp_call_method_n_kw(0, 3, args);
}

static int sdcard_cmd(sdcard_obj_t *self, uint8_t cmd, uint32_t arg, int final, bool release, bool skip1)
{
    sdcard_cs_set(self, 0);

    self->cmdbuf[0] = 0x40 | cmd;
    self->cmdbuf[1] = arg >> 24;
    self->cmdbuf[2] = arg >> 16;
    self->cmdbuf[3] = arg >> 8;
    self->cmdbuf[4] = arg;
    self->cmdbuf[5] = sdcard_crc7(self->cmdbuf, 5) | 0x01;
    sdcard_spi_write_buf(self, self->cmdbuf, sizeof(self->cmdbuf));

    if (skip1)
    {
        sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
    }

    for (size_t i = 0; i < SDCARD_CMD_TIMEOUT; ++i)
    {
        sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
        uint8_t response = self->tokenbuf[0];
        if ((response & 0x80) == 0)
        {
            if (final < 0)
            {
                sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
                final = -1 - final;
            }
            for (int j = 0; j < final; ++j)
            {
                sdcard_spi_write_ff(self);
            }
            if (release)
            {
                sdcard_cs_set(self, 1);
                sdcard_spi_write_ff(self);
            }
            return response;
        }
    }

    sdcard_cs_set(self, 1);
    sdcard_spi_write_ff(self);
    return -1;
}

static bool sdcard_readinto(sdcard_obj_t *self, uint8_t *buf, size_t len)
{
    sdcard_cs_set(self, 0);

    for (size_t i = 0; i < SDCARD_CMD_TIMEOUT; ++i)
    {
        sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
        if (self->tokenbuf[0] == SDCARD_TOKEN_DATA)
        {
            sdcard_spi_write_readinto(self, self->dummybuf, buf, len);
            sdcard_spi_write_ff(self);
            sdcard_spi_write_ff(self);
            sdcard_cs_set(self, 1);
            sdcard_spi_write_ff(self);
            return true;
        }
        mp_hal_delay_ms(1);
    }

    sdcard_cs_set(self, 1);
    sdcard_spi_write_ff(self);
    return false;
}

static bool sdcard_wait_ready(sdcard_obj_t *self)
{
    mp_uint_t start = mp_hal_ticks_ms();
    while (mp_hal_ticks_ms() - start < SDCARD_WRITE_TIMEOUT_MS)
    {
        sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
        if (self->tokenbuf[0] != 0x00)
        {
            return true;
        }
    }
    return false;
}

static bool sdcard_write_data(sdcard_obj_t *self, uint8_t token, const uint8_t *buf)
{
    sdcard_cs_set(self, 0);
    sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), token);
    sdcard_spi_write_buf(self, buf, SDCARD_BLOCK_SIZE);
    sdcard_spi_write_ff(self);
    sdcard_spi_write_ff(self);

    sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), 0xff);
    if ((self->tokenbuf[0] & 0x1f) != 0x05)
    {
        sdcard_cs_set(self, 1);
        sdcard_spi_write_ff(self);
        return false;
    }

    bool ready = sdcard_wait_ready(self);
    sdcard_cs_set(self, 1);
    sdcard_spi_write_ff(self);
    return ready;
}

static bool sdcard_write_token(sdcard_obj_t *self, uint8_t token)
{
    sdcard_cs_set(self, 0);
    sdcard_spi_readinto(self, self->tokenbuf, sizeof(self->tokenbuf), token);
    sdcard_spi_write_ff(self);
    bool ready = sdcard_wait_ready(self);
    sdcard_cs_set(self, 1);
    sdcard_spi_write_ff(self);
    return ready;
}

static void sdcard_init_card_v1(sdcard_obj_t *self)
{
    for (size_t i = 0; i < SDCARD_CMD_TIMEOUT; ++i)
    {
        mp_hal_delay_ms(50);
        sdcard_cmd(self, 55, 0, 0, true, false);
        if (sdcard_cmd(self, 41, 0, 0, true, false) == 0)
        {
            self->cdv = SDCARD_BLOCK_SIZE;
            return;
        }
    }
    mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("timeout waiting for v1 card"));
}

static void sdcard_init_card_v2(sdcard_obj_t *self)
{
    for (size_t i = 0; i < SDCARD_CMD_TIMEOUT; ++i)
    {
        mp_hal_delay_ms(50);
        sdcard_cmd(self, 58, 0, 4, true, false);
        sdcard_cmd(self, 55, 0, 0, true, false);
        if (sdcard_cmd(self, 41, 0x40000000, 0, true, false) == 0)
        {
            sdcard_cmd(self, 58, 0, -4, true, false);
            self->cdv = (self->tokenbuf[0] & 0x40) ? 1 : SDCARD_BLOCK_SIZE;
            return;
        }
    }
    mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("timeout waiting for v2 card"));
}

static void sdcard_init_card(sdcard_obj_t *self, uint32_t baudrate)
{
    sdcard_cs_init(self);
    sdcard_spi_init(self, 100000);

    memset(self->dummybuf, 0xff, sizeof(self->dummybuf));
    for (size_t i = 0; i < 16; ++i)
    {
        sdcard_spi_write_ff(self);
    }

    for (size_t i = 0; i < 5; ++i)
    {
        if (sdcard_cmd(self, 0, 0, 0, true, false) == SDCARD_R1_IDLE_STATE)
        {
            goto card_idle;
        }
    }
    mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("no SD card"));

card_idle:
    switch (sdcard_cmd(self, 8, 0x01aa, 4, true, false))
    {
    case SDCARD_R1_IDLE_STATE:
        sdcard_init_card_v2(self);
        break;
    case SDCARD_R1_IDLE_STATE | SDCARD_R1_ILLEGAL_COMMAND:
        sdcard_init_card_v1(self);
        break;
    default:
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("couldn't determine SD card version"));
    }

    if (sdcard_cmd(self, 9, 0, 0, false, false) != 0)
    {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("no response from SD card"));
    }

    uint8_t csd[16];
    if (!sdcard_readinto(self, csd, sizeof(csd)))
    {
        mp_raise_OSError(MP_ETIMEDOUT);
    }

    switch (csd[0] & 0xc0)
    {
    case 0x40:
        self->sectors = ((((uint32_t)csd[7] << 16) | ((uint32_t)csd[8] << 8) | csd[9]) + 1) * 1024;
        break;
    case 0x00:
    {
        uint32_t c_size = ((csd[6] & 0x03) << 10) | ((uint32_t)csd[7] << 2) | (csd[8] >> 6);
        uint32_t c_size_mult = ((csd[9] & 0x03) << 1) | (csd[10] >> 7);
        uint32_t read_bl_len = csd[5] & 0x0f;
        uint64_t capacity = (uint64_t)(c_size + 1) * (1ull << (c_size_mult + 2)) * (1ull << read_bl_len);
        self->sectors = capacity / SDCARD_BLOCK_SIZE;
        break;
    }
    default:
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("SD card CSD format not supported"));
    }

    if (sdcard_cmd(self, 16, SDCARD_BLOCK_SIZE, 0, true, false) != 0)
    {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("can't set 512 block size"));
    }

    sdcard_spi_init(self, baudrate);
}

static mp_obj_t sdcard_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args)
{
    enum
    {
        ARG_spi,
        ARG_cs,
        ARG_baudrate,
    };
    static const mp_arg_t allowed_args[] = {
        {MP_QSTR_spi, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE}},
        {MP_QSTR_cs, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE}},
        {MP_QSTR_baudrate, MP_ARG_INT, {.u_int = 1320000}},
    };

    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    sdcard_obj_t *self = mp_obj_malloc(sdcard_obj_t, &sdcard_type);
    self->spi = args[ARG_spi].u_obj;
    self->cs = args[ARG_cs].u_obj;
    self->sectors = 0;
    self->cdv = 0;
    sdcard_init_card(self, args[ARG_baudrate].u_int);
    return MP_OBJ_FROM_PTR(self);
}

static void sdcard_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind)
{
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "SDCard(sectors=%u)", (unsigned)self->sectors);
}

static void sdcard_validate_buffer(size_t len)
{
    if (len == 0 || (len % SDCARD_BLOCK_SIZE) != 0)
    {
        mp_raise_ValueError(MP_ERROR_TEXT("buffer length must be a non-zero multiple of 512"));
    }
}

static mp_obj_t sdcard_readblocks(mp_obj_t self_in, mp_obj_t block_num_in, mp_obj_t buf_in)
{
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_WRITE);
    sdcard_validate_buffer(bufinfo.len);

    uint32_t block_num = mp_obj_get_int(block_num_in);
    size_t nblocks = bufinfo.len / SDCARD_BLOCK_SIZE;
    sdcard_spi_write_ff(self);

    if (nblocks == 1)
    {
        if (sdcard_cmd(self, 17, block_num * self->cdv, 0, false, false) != 0)
        {
            sdcard_cs_set(self, 1);
            sdcard_spi_write_ff(self);
            mp_raise_OSError(MP_EIO);
        }
        if (!sdcard_readinto(self, bufinfo.buf, SDCARD_BLOCK_SIZE))
        {
            mp_raise_OSError(MP_ETIMEDOUT);
        }
    }
    else
    {
        if (sdcard_cmd(self, 18, block_num * self->cdv, 0, false, false) != 0)
        {
            sdcard_cs_set(self, 1);
            sdcard_spi_write_ff(self);
            mp_raise_OSError(MP_EIO);
        }
        for (size_t i = 0; i < nblocks; ++i)
        {
            uint8_t *block_buf = (uint8_t *)bufinfo.buf + (i * SDCARD_BLOCK_SIZE);
            if (!sdcard_readinto(self, block_buf, SDCARD_BLOCK_SIZE))
            {
                mp_raise_OSError(MP_ETIMEDOUT);
            }
        }
        if (sdcard_cmd(self, 12, 0, 0, true, true) != 0)
        {
            mp_raise_OSError(MP_EIO);
        }
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_readblocks_obj, sdcard_readblocks);

static mp_obj_t sdcard_writeblocks(mp_obj_t self_in, mp_obj_t block_num_in, mp_obj_t buf_in)
{
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_READ);
    sdcard_validate_buffer(bufinfo.len);

    uint32_t block_num = mp_obj_get_int(block_num_in);
    size_t nblocks = bufinfo.len / SDCARD_BLOCK_SIZE;
    sdcard_spi_write_ff(self);

    if (nblocks == 1)
    {
        if (sdcard_cmd(self, 24, block_num * self->cdv, 0, true, false) != 0)
        {
            mp_raise_OSError(MP_EIO);
        }
        if (!sdcard_write_data(self, SDCARD_TOKEN_DATA, bufinfo.buf))
        {
            mp_raise_OSError(MP_EIO);
        }
    }
    else
    {
        if (sdcard_cmd(self, 25, block_num * self->cdv, 0, true, false) != 0)
        {
            mp_raise_OSError(MP_EIO);
        }
        for (size_t i = 0; i < nblocks; ++i)
        {
            const uint8_t *block_buf = (const uint8_t *)bufinfo.buf + (i * SDCARD_BLOCK_SIZE);
            if (!sdcard_write_data(self, SDCARD_TOKEN_CMD25, block_buf))
            {
                mp_raise_OSError(MP_EIO);
            }
        }
        if (!sdcard_write_token(self, SDCARD_TOKEN_STOP_TRAN))
        {
            mp_raise_OSError(MP_ETIMEDOUT);
        }
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_writeblocks_obj, sdcard_writeblocks);

static mp_obj_t sdcard_ioctl(mp_obj_t self_in, mp_obj_t cmd_in, mp_obj_t arg_in)
{
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    switch (mp_obj_get_int(cmd_in))
    {
    case MP_BLOCKDEV_IOCTL_INIT:
    case MP_BLOCKDEV_IOCTL_DEINIT:
    case MP_BLOCKDEV_IOCTL_SYNC:
        return MP_OBJ_NEW_SMALL_INT(0);
    case MP_BLOCKDEV_IOCTL_BLOCK_COUNT:
        return mp_obj_new_int_from_uint(self->sectors);
    case MP_BLOCKDEV_IOCTL_BLOCK_SIZE:
        return MP_OBJ_NEW_SMALL_INT(SDCARD_BLOCK_SIZE);
    default:
        return mp_const_none;
    }
}
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_ioctl_obj, sdcard_ioctl);

static const mp_rom_map_elem_t sdcard_locals_dict_table[] = {
    {MP_ROM_QSTR(MP_QSTR_readblocks), MP_ROM_PTR(&sdcard_readblocks_obj)},
    {MP_ROM_QSTR(MP_QSTR_writeblocks), MP_ROM_PTR(&sdcard_writeblocks_obj)},
    {MP_ROM_QSTR(MP_QSTR_ioctl), MP_ROM_PTR(&sdcard_ioctl_obj)},
};
static MP_DEFINE_CONST_DICT(sdcard_locals_dict, sdcard_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    sdcard_type,
    MP_QSTR_SDCard,
    MP_TYPE_FLAG_NONE,
    make_new, sdcard_make_new,
    print, sdcard_print,
    locals_dict, &sdcard_locals_dict);

static const mp_rom_map_elem_t sdcard_module_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sdcard)},
    {MP_ROM_QSTR(MP_QSTR_SDCard), MP_ROM_PTR(&sdcard_type)},
};
static MP_DEFINE_CONST_DICT(sdcard_module_globals, sdcard_module_globals_table);

const mp_obj_module_t sdcard_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&sdcard_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_sdcard, sdcard_module);
