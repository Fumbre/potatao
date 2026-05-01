#include "sdcard.h"     // C++ class
#include "sdcard_api.h" // C API declarations
#include "pico/stdlib.h"
#include "pico/types.h"
#include "hardware/gpio.h"
#include "hardware/spi.h"

/* ---------------------------------------------------------------
 * Constructor / Destructor
 * --------------------------------------------------------------- */
SDCard::SDCard(spi_inst_t *spi,
               uint sck,
               uint mosi,
               uint miso,
               uint cs)
    : _spi(spi),
      _sck(sck),
      _mosi(mosi),
      _miso(miso),
      _cs(cs),
      is_mounted(false),
      is_sdhc(true)
{
}

SDCard::~SDCard()
{
    unmount();
}

/* ---------------------------------------------------------------
 * mount
 * Initialize SPI + GPIO and run the SD card power-up sequence.
 * --------------------------------------------------------------- */
bool SDCard::mount()
{
    if (is_mounted)
        return true;

    gpio_set_function(_sck, GPIO_FUNC_SPI);
    gpio_set_function(_mosi, GPIO_FUNC_SPI);
    gpio_set_function(_miso, GPIO_FUNC_SPI);

    gpio_init(_cs);
    gpio_set_dir(_cs, GPIO_OUT);
    gpio_put(_cs, 1);

    spi_init(_spi, 400 * 1000);

    // Send at least 74 dummy clocks to let the card finish its internal power-up
    uint8_t dummy = 0xFF;
    for (int i = 0; i < 10; i++)
    {
        spi_write_blocking(_spi, &dummy, 1);
    }

    if (!physical_init())
    {
        return false;
    }

    spi_set_baudrate(_spi, 12 * 1000 * 1000);

    is_mounted = true;
    return true;
}

/* ---------------------------------------------------------------
 * unmount
 * --------------------------------------------------------------- */
bool SDCard::unmount()
{
    if (!is_mounted)
        return true;

    gpio_put(_cs, 1);
    is_mounted = false;
    return true;
}

/* ---------------------------------------------------------------
 * exist
 * File system awareness lives in the upper layer; always false here.
 * --------------------------------------------------------------- */
bool SDCard::exist(const char *path)
{
    (void)path;
    return false;
}

/* ---------------------------------------------------------------
 * get_spi
 * --------------------------------------------------------------- */
spi_inst_t *SDCard::get_spi()
{
    return _spi;
}

/* ---------------------------------------------------------------
 * send_cmd
 * Send one SD command and return the R1 response byte.
 * --------------------------------------------------------------- */
uint8_t SDCard::send_cmd(uint8_t cmd, uint32_t arg)
{
    uint8_t packet[6];

    packet[0] = cmd | 0x40;
    packet[1] = (uint8_t)(arg >> 24);
    packet[2] = (uint8_t)(arg >> 16);
    packet[3] = (uint8_t)(arg >> 8);
    packet[4] = (uint8_t)(arg);

    // CMD0 and CMD8 require valid CRC; all others use stop-bit only
    if (cmd == CMD0)
        packet[5] = 0x95;
    else if (cmd == CMD8)
        packet[5] = 0x87;
    else
        packet[5] = 0x01;

    spi_write_blocking(_spi, packet, 6);

    uint8_t res;
    int retry = 100;
    do
    {
        spi_read_blocking(_spi, 0xFF, &res, 1);
    } while (res == 0xFF && retry-- > 0);

    return res;
}

/* ---------------------------------------------------------------
 * physical_init
 * Execute the CMD0 / CMD8 / ACMD41 initialization handshake.
 * --------------------------------------------------------------- */
bool SDCard::physical_init()
{
    uint8_t res;

    // Release any previous transaction
    gpio_put(_cs, 1);
    uint8_t dummy = 0xFF;
    spi_write_blocking(_spi, &dummy, 1);

    // CMD0: software reset, enter SPI mode
    gpio_put(_cs, 0);
    res = send_cmd(CMD0, 0);
    gpio_put(_cs, 1);

    if (res != 0x01)
        return false;

    // CMD8: check for SDv2 (SDHC/SDXC)
    gpio_put(_cs, 0);
    res = send_cmd(CMD8, 0x1AA);

    if (res == 0x01)
    {
        is_sdhc = true;
        uint8_t buf[4];
        spi_read_blocking(_spi, 0xFF, buf, 4); // discard R7 trailing bytes
    }
    else
    {
        is_sdhc = false;
    }
    gpio_put(_cs, 1);

    // ACMD41: wait for the card to finish initialization
    int retry = 2000;
    do
    {
        gpio_put(_cs, 0);
        send_cmd(CMD55, 0);
        res = send_cmd(ACMD41, is_sdhc ? 0x40000000 : 0);
        gpio_put(_cs, 1);

        if (res == 0x00)
            break;
        sleep_ms(1);
    } while (retry-- > 0);

    return (res == 0x00);
}

/* ---------------------------------------------------------------
 * read_blocks
 * Read `count` 512-byte sectors starting at `sector`.
 * --------------------------------------------------------------- */
int SDCard::read_blocks(uint8_t *buff,
                        uint32_t sector,
                        uint32_t count)
{
    for (uint32_t i = 0; i < count; i++)
    {

        // SDHC uses sector addressing; SDSC uses byte addressing
        uint32_t addr = is_sdhc ? (sector + i) : ((sector + i) << 9);

        gpio_put(_cs, 0);

        if (send_cmd(CMD17, addr) != 0x00)
        {
            gpio_put(_cs, 1);
            return SD_ERROR;
        }

        // Wait for the data start token 0xFE
        uint8_t token = 0xFF;
        int timeout = 5000;
        while (token != 0xFE && timeout--)
        {
            spi_read_blocking(_spi, 0xFF, &token, 1);
        }

        if (token != 0xFE)
        {
            gpio_put(_cs, 1);
            return SD_ERROR;
        }

        spi_read_blocking(_spi, 0xFF, buff + (i * 512), 512);

        // Read and discard the 2-byte CRC
        uint8_t crc[2];
        spi_read_blocking(_spi, 0xFF, crc, 2);

        gpio_put(_cs, 1);

        // Extra byte after CS de-assert to release the bus
        uint8_t dummy2 = 0xFF;
        spi_write_blocking(_spi, &dummy2, 1);
    }

    return SD_OK;
}

/* ---------------------------------------------------------------
 * write_blocks
 * Write `count` 512-byte sectors starting at `sector`.
 * --------------------------------------------------------------- */
int SDCard::write_blocks(const uint8_t *buff,
                         uint32_t sector,
                         uint32_t count)
{
    for (uint32_t i = 0; i < count; i++)
    {

        uint32_t addr = is_sdhc ? (sector + i) : ((sector + i) << 9);

        gpio_put(_cs, 0);

        if (send_cmd(CMD24, addr) != 0x00)
        {
            gpio_put(_cs, 1);
            return SD_ERROR;
        }

        // Data start token
        uint8_t start = 0xFE;
        spi_write_blocking(_spi, &start, 1);

        spi_write_blocking(_spi, buff + (i * 512), 512);

        // Dummy CRC (not checked)
        uint8_t crc[2] = {0xFF, 0xFF};
        spi_write_blocking(_spi, crc, 2);

        // Data response token: lower 5 bits == 0b00101 means accepted
        uint8_t resp;
        spi_read_blocking(_spi, 0xFF, &resp, 1);

        if ((resp & 0x1F) != 0x05)
        {
            gpio_put(_cs, 1);
            return SD_ERROR;
        }

        // Wait while the card is busy (busy == 0x00)
        uint8_t busy;
        int timeout = 500000;
        do
        {
            spi_read_blocking(_spi, 0xFF, &busy, 1);
        } while (busy == 0x00 && timeout-- > 0);

        gpio_put(_cs, 1);

        if (busy == 0x00)
            return SD_ERROR; // timed out
    }

    return SD_OK;
}

/* ---------------------------------------------------------------
 * ioctl — minimal device control
 * --------------------------------------------------------------- */
int SDCard::ioctl(uint8_t cmd, void *buff)
{
    switch (cmd)
    {
    case CTRL_SYNC:
        return SD_OK;

    case GET_SECTOR_SIZE:
        *(uint32_t *)buff = 512;
        return SD_OK;

    default:
        return SD_PARERR;
    }
}

/* ---------------------------------------------------------------
 * C API
 * --------------------------------------------------------------- */
extern "C"
{

    void *sdcard_new(int spi_id,
                     unsigned int sck,
                     unsigned int mosi,
                     unsigned int miso,
                     unsigned int cs)
    {
        // spi0 and spi1 are defined by hardware/spi.h from the Pico SDK
        spi_inst_t *spi = (spi_id == 0) ? spi0 : spi1;
        return new SDCard(spi, sck, mosi, miso, cs);
    }

    void sdcard_destroy(void *self)
    {
        delete static_cast<SDCard *>(self);
    }

    int sdcard_disk_init(void *self)
    {
        return static_cast<SDCard *>(self)->mount() ? SD_OK : SD_ERROR;
    }

    int sdcard_disk_read(void *self,
                         uint8_t *buff,
                         uint32_t sector,
                         uint32_t count)
    {
        return static_cast<SDCard *>(self)->read_blocks(buff, sector, count);
    }

    int sdcard_disk_write(void *self,
                          const uint8_t *buff,
                          uint32_t sector,
                          uint32_t count)
    {
        return static_cast<SDCard *>(self)->write_blocks(buff, sector, count);
    }

    int sdcard_disk_ioctl(void *self, uint8_t cmd, uint32_t arg)
    {
        uint32_t result = 0;
        int ret = static_cast<SDCard *>(self)->ioctl(cmd, &result);
        if (cmd == GET_SECTOR_SIZE && ret == SD_OK)
        {
            return (int)result;
        }
        return ret;
    }

} // extern "C"