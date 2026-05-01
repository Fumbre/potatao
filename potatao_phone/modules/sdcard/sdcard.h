#pragma once

#include <stdint.h>
#include "pico/stdlib.h"
#include "pico/types.h"
#include "hardware/spi.h"

/* ---------------------------------------------------------------
 * SD commands
 * --------------------------------------------------------------- */
#define CMD0    0
#define CMD8    8
#define CMD17   17
#define CMD24   24
#define CMD55   55
#define ACMD41  41

/* ---------------------------------------------------------------
 * ioctl commands
 * --------------------------------------------------------------- */
#define CTRL_SYNC       0
#define GET_SECTOR_SIZE 1

/* ---------------------------------------------------------------
 * Return values
 * --------------------------------------------------------------- */
#define SD_OK       0
#define SD_ERROR    1
#define SD_PARERR   2

/* ---------------------------------------------------------------
 * SDCard class
 * --------------------------------------------------------------- */
class SDCard {
public:
    SDCard(spi_inst_t *spi,
           uint sck,
           uint mosi,
           uint miso,
           uint cs);
    ~SDCard();

    bool mount();
    bool unmount();
    bool exist(const char *path);

    spi_inst_t* get_spi();

    int read_blocks(uint8_t *buff, uint32_t sector, uint32_t count);
    int write_blocks(const uint8_t *buff, uint32_t sector, uint32_t count);
    int ioctl(uint8_t cmd, void *buff);

private:
    bool    physical_init();
    uint8_t send_cmd(uint8_t cmd, uint32_t arg);

    spi_inst_t *_spi;
    uint _sck, _mosi, _miso, _cs;

    bool is_mounted;
    bool is_sdhc;
};

/* ---------------------------------------------------------------
 * C API
 * Use unsigned int instead of uint so pure-C callers can include
 * this header without pulling in pico/types.h.
 * --------------------------------------------------------------- */
#ifdef __cplusplus
extern "C" {
#endif

void* sdcard_new(int spi_id,
                 unsigned int sck,
                 unsigned int mosi,
                 unsigned int miso,
                 unsigned int cs);
void  sdcard_destroy(void *self);
int   sdcard_disk_init(void *self);
int   sdcard_disk_read(void *self, uint8_t *buff, uint32_t sector, uint32_t count);
int   sdcard_disk_write(void *self, const uint8_t *buff, uint32_t sector, uint32_t count);

#ifdef __cplusplus
}
#endif