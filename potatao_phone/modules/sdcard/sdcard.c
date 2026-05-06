#include "py/runtime.h"
#include "py/obj.h"
#include "py/mphal.h"

#include "hardware/pio.h"
#include "hardware/clocks.h"

#include "sdcard.pio.h"

// --------------------------------- C ---------------------------------------------

// SPI protocol command constant
#define CMD0   (0)      // reset
#define CMD8   (8)      // check voltage (important for SDHC/SDXC)
#define CMD17  (17)     // read block
#define CMD24  (24)     // write block
#define ACMD41 (41)     // active initalization
#define CMD55  (55)     // ACMD previous command
#define CMD58  (58)     // read OCR

// define sdcard c struct
typedef struct _sdcard_obj_t{
    mp_obj_base_t base; // this property must be in the first position, micropython can recognize this struct as micropython object
    PIO pio; // in pico 2 w, there has pio0 and pio1
    uint sm; // state machine  In order to support multiple sdcard
    uint offset; // the starting line in pio file
    uint sck;
    uint mosi;
    uint miso;
    uint cs;
    bool is_sdhc;
} sdcard_obj_t;

/**
 *  init PIO and sdcard
 */
static void sdcard_pio_init(sdcard_obj_t *self, uint baudrate){
    // load pio
    self->offset = pio_add_program_at_offset(self->pio, &sdcard_program);
    //init state machine
    self->sm = pio_claim_unused_sm(self->pio,true);
    //get configuration from pio
    pio_sm_config pio_config = sdcard_program_get_default_config(self->offset);
    // init sdcard pins
    //bind MOSI pin
    sm_config_set_out_pins(&pio_config,self->mosi,1);
    //bind SCK pin
    sm_config_set_sideset_pins(&pio_config,self->sck);
    //bind MISO pin
    sm_config_set_in_pins(&pio_config,self->miso);
    // define pins directions
    // true is high voltage, otherwise it's low voltage.
    pio_sm_set_consecutive_pindirs(self->pio, self->sm, self->mosi, 1, true);
    pio_sm_set_consecutive_pindirs(self->pio, self->sm, self->sck, 1, true);
    pio_sm_set_consecutive_pindirs(self->pio, self->sm, self->miso, 1, false);
    //build connection between pio and GPIO
    pio_gpio_init(self->pio,self->miso);
    gpio_pull_up(self->miso);
    pio_gpio_init(self->pio,self->mosi);
    pio_gpio_init(self->pio,self->sck);
    //config shift register
    sm_config_set_out_shift(&pio_config,false,true,8);
    sm_config_set_in_shift(&pio_config,true,true,8);
    //config clock frequency
    float div = (float)clock_get_hz(clk_sys) / (baudrate * 2);
    sm_config_set_clkdiv(&pio_config, div);
    //start
    pio_sm_init(self->pio,self->sm,self->offset,&pio_config);
    pio_sm_set_enabled(self->pio,self->sm,true);
}

/**
 * @name pio_read_write_byte
 * @author Sunny
 * @param self sdcard C instance
 * @param data the data from 
 */
static uint8_t pio_read_write_byte(sdcard_obj_t *self, uint8_t data){
    // pio send data to FIFO TX caching pool
    pio_sm_put_blocking(self->pio,self->sm,(uint32_t)data<<24);
    //pio get data from FIFO RX
    return (uint8_t)(pio_sm_get_blocking(self->pio, self->sm) & 0xFF);
}

/**
 * @name sdcard_select
 * @author Sunny
 * @date 06-05-2026
 * @details active sdcard
 */
static void sdcard_select(sdcard_obj_t *self){
    mp_hal_pin_low(self->cs);
}

/**
 * @name sdcard_deselect
 * @author Sunny
 * @date 06-05-2026
 * @details disconnect sdcard
 */
static void sdcard_deselect(sdcard_obj_t *self){
    mp_hal_pin_high(self->cs);
    pio_read_write_byte(self, 0xFF); // wait SPI release
}

/**
 * @name sdcard_cmd_send
 * @author Sunny
 * @date 06-05-2026
 * @details send commands to SPI
 * @param self sdcard instance
 * @param cmd SPI command
 * @param arg content of command
 */
static uint8_t sdcard_cmd_send(sdcard_obj_t *self, uint8_t cmd, uint32_t arg){
    // wait until sdcard is ready
    if (cmd != CMD0){
        for (int i = 0; i < 500; i++) {
            if (pio_read_write_byte(self, 0xFF) == 0xFF) break;
            mp_hal_delay_ms(1);
        }
    }
    // send command package 
    pio_read_write_byte(self, 0x40 | cmd); // start a new command
    //cut 32 digital data to 4 parts. because SPI can only support 8 digit
    pio_read_write_byte(self, arg >> 24); 
    pio_read_write_byte(self, arg >> 16);
    pio_read_write_byte(self, arg >> 8);
    pio_read_write_byte(self, arg);

    //send verified code to SPI. if commands are CMD0 and CMD8
    uint8_t crc = 0xFF; //
    if (cmd == CMD0) crc = 0x95;
    else if (cmd == CMD8) crc = 0x87;
    pio_read_write_byte(self, crc);
    //get SPI response 
    for (int i = 0; i < 100; i++) {
        uint8_t res = pio_read_write_byte(self, 0xFF);// get SPI response
        if (!(res & 0x80)) return res; //check response data whether it is valid
    }
    return 0xFF; // time out
}

/**
 * @name init_sdcard
 * @author Sunny
 * @date 06-05-2026
 */
static void init_sdcard(sdcard_obj_t *self){
    // start sdcard in low baudrate
    float div_low = (float) clock_get_hz(clk_sys) / (400000 * 2);
    pio_sm_set_clkdiv(self->pio,self->sm,div_low);
    //let sdcard make connection with SPI
    sdcard_deselect(self);
    for (int i = 0; i < 10; i++) pio_read_write_byte(self, 0xFF);
    //enter the free mode
    if (sdcard_cmd_send(self, CMD0, 0) != 0x01) return;
    //recognize sdcard type
    if (sdcard_cmd_send(self, CMD8, 0x1AA) == 0x01) {
        for (int i = 0; i < 4; i++) pio_read_write_byte(self, 0xFF);
        while (true) {
            sdcard_cmd_send(self, CMD55, 0);
            if (sdcard_cmd_send(self, ACMD41, 0x40000000) == 0x00) break;
            mp_hal_delay_ms(1);
        }
        if (sdcard_cmd_send(self, CMD58, 0) == 0x00) {
            uint8_t ocr0 = pio_read_write_byte(self, 0xFF);
            self->is_sdhc = (ocr0 & 0x40) ? true : false;
            for (int i = 0; i < 3; i++) pio_read_write_byte(self, 0xFF);
        }
    }
    float div_high = (float)clock_get_hz(clk_sys) / (12000000 * 2);
    pio_sm_set_clkdiv(self->pio, self->sm, div_high);
    sdcard_deselect(self);
}

// ------------------------------------ MicroPython -----------------------------------------

/**
 * @name constructer function
 * @author Sunny 
 * @date 06-05-2026
 * @param type data type, in this case, it's sdcard
 * @param args_number arguments position number
 * @param kw_number argument value number
 * @param args argment value
 */
static mp_obj_t sdcard_make_new(const mp_obj_empty_type_t *type, size_t args_number, size_t kw_number, const mp_obj_t *args){
    //check the argument number
    mp_arg_check_num(args_number,kw_number,6,6,false);
    //create object RAM address
    sdcard_obj_t *self = mp_obj_malloc(sdcard_obj_t,type);
    //convert micropython data type to C data type
    uint pio = mp_obj_get_int(args[0]);
    self->pio = (pio == 0)? pio0:pio1;
    self->sck = mp_obj_get_int(args[1]);
    self->mosi = mp_obj_get_int(args[2]);
    self->miso = mp_obj_get_int(args[3]);
    self->cs = mp_obj_get_int(args[4]);
    uint baudrate = mp_obj_get_int(args[5]);

    mp_hal_pin_output(self->cs);
    mp_hal_pin_high(self->cs);
    //init pins
    sdcard_pio_init(self,baudrate);
    //return micropython object
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t scard_read_blocks(mp_obj_t self_in, mp_obj_t block_num, mp_obj_t buffer){
    // get sdcard c struct
    sdcard_obj_t *self = MP_OBJ_TO_PTR(self_in);
    //get block number with C
    uint32_t b_num = mp_obj_get_int(block_num);
    // get data buffer with C
    mp_buffer_info_t buffer_info;
    mp_get_buffer_raise(buffer,&buffer_info,MP_BUFFER_WRITE);
    //check sdcard type
    uint32_t addr = self->is_sdhc ? b_num : b_num * 512;
    sdcard_select(self);
    if (sdcard_cmd_send(self, CMD17, addr) != 0x00) {
        sdcard_deselect(self);
        return mp_const_false;
    }
    while (pio_read_write_byte(self, 0xFF) != 0xFE);
    uint8_t *buf = buffer_info.buf;
    for (size_t i = 0; i < buffer_info.len; i++) {
        *buf++ = pio_read_write_byte(self, 0xFF);
    }
    pio_read_write_byte(self, 0xFF);
    pio_read_write_byte(self, 0xFF);

    sdcard_deselect(self);
    return mp_const_true;
}
//convert c function into micropython function object
static MP_DEFINE_CONST_FUN_OBJ_3(sdcard_read_blocks_obj,scard_read_blocks);

//define micropython dicts about sdcard
//MP_ROM_QSTR: define customized key. Tips: "MP_QSTR_" is the mandortary prefix in key. Because micropython depends on this prefix to recognize.
//MP_ROM_PTR: key's value
static mp_rom_map_elem_t sdcard_dict_table[] = {
    {MP_ROM_QSTR(MP_QSTR_sdcard_read_blocks), MP_ROM_PTR(&sdcard_read_blocks_obj)},
};
static MP_DEFINE_CONST_DICT(sdcard_dict,sdcard_dict_table);

//define micropython sdcard object
MP_DEFINE_CONST_OBJ_TYPE(
    sdcard_type,
    MP_QSTR_SDCard,
    MP_TYPE_FLAG_NONE,
    make_new,sdcard_make_new,
    locals_dict, &sdcard_dict
);