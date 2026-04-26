#ifndef SDCARD_H
#define SDCARD_H

#pragma once

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include <stdint.h>
#include "pico/binary_info.h"
#ifndef uint
typedef unsigned int uint;
#endif

#ifdef __cplusplus
extern "C" {
#endif

    #include "ff.h"
    #include "diskio.h"

    /* Wrapper functions for MicroPython C Module */
    void* sdcard_new(int spi_id, uint sck, uint mosi, uint miso, uint cs);
    void  sdcard_destroy(void* self);
    int   sdcard_disk_init(void* self);
    int   sdcard_disk_read(void* self, uint8_t* buff, uint32_t sector, uint32_t count);
    int   sdcard_disk_write(void* self, const uint8_t* buff, uint32_t sector, uint32_t count);

#ifdef __cplusplus
}
#endif

#ifdef __cplusplus

#include <string>
#include <vector>

#define CMD0    0   /* GO_IDLE_STATE */
#define CMD1    1   /* SEND_OP_COND (MMC) */
#define CMD8    8   /* SEND_IF_COND */
#define CMD9    9   /* SEND_CSD */
#define CMD10   10  /* SEND_CID */
#define CMD12   12  /* STOP_TRANSMISSION */
#define CMD16   16  /* SET_BLOCKLEN */
#define CMD17   17  /* READ_SINGLE_BLOCK */
#define CMD18   18  /* READ_MULTIPLE_BLOCK */
#define CMD23   23  /* SET_BLOCK_COUNT (MMC) */
#define CMD24   24  /* WRITE_BLOCK */
#define CMD25   25  /* WRITE_MULTIPLE_BLOCK */
#define CMD41   41  /* SEND_OP_COND (ACMD) */
#define CMD55   55  /* APP_CMD */
#define CMD58   58  /* READ_OCR */
#define ACMD41  41

/**
 * @name SDcard interface class
 * @author Sunny
 * @date 21-04-2026
 */
class SDCard {
public:
    SDCard(spi_inst_t *spi, uint sck, uint mosi, uint miso, uint cs, bool is_sdhc = true);
    ~SDCard();

    bool mount();
    bool physical_init();
    bool unmount();
    bool exist(const std::string& path);
    
    spi_inst_t* get_spi();
    
    bool is_sdhc;
    uint _cs;
    uint _sck;
    uint _mosi;
    uint _miso;

    BYTE send_cmd(BYTE cmd, DWORD arg);

private:
    spi_inst_t *_spi;
    FATFS fs;
    bool is_mounted;
    FRESULT last_result;
};

#endif /* __cplusplus */

#endif /* SDCARD_H */