#pragma once
#include <stdint.h>

#define SD_OK 0
#define SD_ERROR 1
#define SD_PARERR 2

#define CTRL_SYNC 0
#define GET_SECTOR_SIZE 1

#ifdef __cplusplus
extern "C"
{
#endif

    void *sdcard_new(int spi_id, unsigned int sck, unsigned int mosi,
                     unsigned int miso, unsigned int cs);
    void sdcard_destroy(void *self);
    int sdcard_disk_init(void *self);
    int sdcard_disk_read(void *self, uint8_t *buff, uint32_t sector, uint32_t count);
    int sdcard_disk_write(void *self, const uint8_t *buff, uint32_t sector, uint32_t count);
    int sdcard_disk_ioctl(void *self, uint8_t cmd, uint32_t arg);

#ifdef __cplusplus
}
#endif