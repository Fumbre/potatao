#pragma once
#ifdef __cplusplus

#include <stdint.h>
#include "pico/stdlib.h"
#include "pico/types.h"
#include "hardware/spi.h"

#define CMD0 0
#define CMD8 8
#define CMD17 17
#define CMD24 24
#define CMD55 55
#define ACMD41 41

#define CTRL_SYNC 0
#define GET_SECTOR_SIZE 1

#define SD_OK 0
#define SD_ERROR 1
#define SD_PARERR 2

class SDCard
{
public:
    SDCard(spi_inst_t *spi, uint sck, uint mosi, uint miso, uint cs);
    ~SDCard();
    bool mount();
    bool unmount();
    bool exist(const char *path);
    spi_inst_t *get_spi();
    int read_blocks(uint8_t *buff, uint32_t sector, uint32_t count);
    int write_blocks(const uint8_t *buff, uint32_t sector, uint32_t count);
    int ioctl(uint8_t cmd, void *buff);

private:
    bool physical_init();
    uint8_t send_cmd(uint8_t cmd, uint32_t arg);
    spi_inst_t *_spi;
    uint _sck, _mosi, _miso, _cs;
    bool is_mounted;
    bool is_sdhc;
};

#endif // __cplusplus