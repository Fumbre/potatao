/**
 * @name SDCard impliment
 * @author Sunny
 * @date 21-04-2026
 */
#include "sdcard.h"

/**
 * @name constructor function
 * @author Sunny
 * @date 21-04-2026
 * 
 */
SDCard::SDCard(spi_inst_t *spi, uint sck, uint mosi, uint miso, uint cs, bool is_sdhc)
       : _spi(spi), _sck(sck), _mosi(mosi), _miso(miso), _cs(cs), is_mounted(false), is_sdhc(is_sdhc) {
       }

/**
 * @name Desctructor function
 * @author Sunny
 * @date 21-04-2026
 */
SDCard::~SDCard(){
    unmount();
}

/**
 * @name mount
 * @author Sunny
 * @date 21-04-2026
 * @details init pins which is related to SDCard and make a connection between SDCard and PICO 2 W
 */
bool SDCard::mount(){
    if (is_mounted) return true;
    //mention sck, mosi, miso that focus on SPI protocol
    gpio_set_function(_sck,GPIO_FUNC_SPI);
    gpio_set_function(_mosi,GPIO_FUNC_SPI);
    gpio_set_function(_miso,GPIO_FUNC_SPI);
    //open software control
    gpio_init(_cs);
    gpio_set_dir(_cs, GPIO_OUT);
    gpio_put(_cs, 1);
    //init SPI protocol, define the inital frequency (it base on SPI security)
    spi_init(_spi, 400 * 1000);
    BYTE dummy = 0xFF;
    for(int i = 0; i < 10; i++) spi_write_blocking(_spi, &dummy, 1);
    if (!physical_init()) {
        return false; 
    }
    //call FatFs mount SDCard
    last_result = f_mount(&fs);
    if(last_result == FR_OK){
        //switch SPI frequency to high frequency
        is_mounted = true;
        spi_set_baudrate(_spi,12*1000*1000);
        return true;
    }
    return false;
}

/**
 * @name unmount
 * @author Sunny
 * @date 21-04-2026
 */
bool SDCard::unmount(){
    if(!is_mounted) return true;
    //call FatFs to disconnect between SDcard and Pico 2 W
    last_result = f_mount(nullptr);
    if(last_result == FR_OK){
        is_mounted = false;
        gpio_put(_cs,1);
        return true;
    }
    return false;
}

/**
 * @name send_cmd
 * @author Sunny
 * @date 21-04-2026
 * @param cmd command (reset(CMD0), read(CMD17), write(CMD24), check(CMD8))
 * @param arg targeted file partition address
 * @return return SDCard R1 response (e.g: 0x00 represent success, 0xFF represent no response)
 * @details check targeted file partition address status
 */
BYTE SDCard::send_cmd(BYTE cmd, DWORD arg){
    //construct 6 byte command package
    BYTE package[6];
    package[0] = cmd | 0x40; //command start (According to SDCard, the first 2 digits of starting command must be 01!)
    //split args to 4 parts, because SPI only can send 8 digit data every time, and arg has 32 digit. So it should split 4 parts.
    //send data by correct sort, from high to low.
    package[1] = (BYTE)(arg >> 24);
    package[2] = (BYTE)(arg >> 16);
    package[3] = (BYTE)(arg >> 8);
    package[4] = (BYTE)arg;
    // set stop command
    if (cmd == CMD0) package[5] = 0x95;
    else if (cmd == CMD8) package[5] = 0x87;
    else package[5] = 0x01;
    //send a complete data package
    spi_write_blocking(_spi,package,6);
    //wait R1 response
    BYTE res;
    int retry = 100;
    do
    {
        spi_read_blocking(_spi,0xFF,&res,1);
    } while (res == 0xFF && retry-- > 0);
    return res;
}

/**
 * @name exist
 * @author Sunny
 * @date 21-04-2026
 * @param path file path in SDcard
 */
bool SDCard::exist(const std::string& path){
    FILINFO fno; // basic file inforamtion structure in SDCard
    last_result = f_stat(&fs,path.c_str(),&fno);
    return (last_result == FR_OK);
}

/**
 * @name get_spi
 * @author Sunny
 * @date 21-04-2026
 * @details get SPI object
 */
spi_inst_t* SDCard::get_spi(){
    return this->_spi;
}


bool SDCard::physical_init(){
    BYTE res;
    //send CMD0 to enter the SPI
    gpio_put(_cs,0);
    res = send_cmd(CMD0,0);//reset
    gpio_put(_cs,1);
    //check whether its enter the SPI
    if (res != 0x01) return false;
    //send CMD8 to check voltage and card version
    gpio_put(_cs, 0);
    res = send_cmd(CMD8, 0x1AA);
    if(res  == 0x01){
        is_sdhc = true;
        BYTE buffer[4];
        spi_read_blocking(_spi,0xFF,buffer,4);
    }else{
        is_sdhc = false;
    }
    gpio_put(_cs,1);

    //active card working model
    int retry = 2000;
    do{
        gpio_put(_cs, 0);
        send_cmd(CMD55, 0);
        res = send_cmd(ACMD41, is_sdhc ? 0x40000000 : 0);
        gpio_put(_cs, 1);
        if(res == 0x00) break;
        sleep_ms(1);
    }while(retry --> 0);
    return (res == 0x00);
}


extern "C" {

    /**
     * @name disk_read
     * @details
     */
    DRESULT disk_read(void* drv, BYTE* buff, DWORD sector, UINT count){
        //convert drv into SDCard pointer
        SDCard* sd = static_cast<SDCard*>(drv);
        // get SPI object 
        spi_inst_t* spi = sd->get_spi();
        //check whether SDcard and SPI exists
        if(!sd || !spi) return RES_ERROR;
        //read file by every partition(In SDcard, every partition has 512 bytes)
        for(UINT i = 0; i < count; i++){
           // caculate address
           DWORD addr = sd->is_sdhc ? (sector + i) : ((sector + i) << 9);
           // select SDCard partition 
           gpio_put(sd->_cs,0);
           //send reading command
           if(sd->send_cmd(CMD17,addr) != 0x00){
            gpio_put(sd->_cs, 1);
            return RES_ERROR;
           }
           //waitting SDCard ready to transmit data
           BYTE token = 0xFF;
           int timeout = 5000;
           while(token != 0xFE && timeout-->0){
            spi_read_blocking(spi,0xFF,&token,1);
           }
           
           if(token != 0XFE){
            gpio_put(sd->_cs,1);
            return RES_ERROR;
           }
           //read file from SD card
           spi_read_blocking(spi,0xFF,buff + (i * 512), 512);
           // read and ignore 2 bytes of CRC check
           BYTE crc[2];
           spi_read_blocking(spi, 0xFF, crc, 2);
           // close block
           gpio_put(sd->_cs, 1);
           // waitting pico 2 w finish reading
           BYTE dummy = 0xFF;
           spi_write_blocking(spi, &dummy, 1);
        }
        return RES_OK;
    }

    /**
     * @name disk_write
     * @details
     */
    DRESULT disk_write(void* drv, const BYTE* buff, DWORD sector, UINT count){
        SDCard* sd = static_cast<SDCard*>(drv);
        spi_inst_t* spi = sd->get_spi();
        if (!sd || !spi) return RES_ERROR;
        for (UINT i = 0; i < count; i++) {
            DWORD addr = sd->is_sdhc ? (sector + i) : ((sector + i) << 9);
            gpio_put(sd->_cs, 0);
            if (sd->send_cmd(CMD24, addr) != 0x00) {
                gpio_put(sd->_cs, 1);
                return RES_ERROR;
            }
            BYTE start_token = 0xFE;
            spi_write_blocking(spi, &start_token, 1);
            spi_write_blocking(spi, (BYTE*)buff + (i * 512), 512);
            BYTE dummy_crc[2] = {0xFF, 0xFF};
            spi_write_blocking(spi, dummy_crc, 2);
            BYTE res;
            spi_read_blocking(spi, 0xFF, &res, 1);
            if ((res & 0x1F) != 0x05) {
                gpio_put(sd->_cs, 1);
                return RES_ERROR;
            }
            BYTE busy;
            int timeout = 500000;
            do {
                spi_read_blocking(spi, 0xFF, &busy, 1);
            } while (busy == 0x00 && timeout-- > 0);
            gpio_put(sd->_cs, 1);
            BYTE dummy = 0xFF;
            spi_write_blocking(spi, &dummy, 1);
            if (busy == 0x00) return RES_ERROR;
        }
        return RES_OK;
    }


    void* sdcard_new(int spi_id, uint sck, uint mosi, uint miso, uint cs) {
        spi_inst_t *spi = (spi_id == 0) ? spi0 : spi1;
        return new SDCard(spi, sck, mosi, miso, cs, true);
    }

    void sdcard_destroy(void* self) {
        if (self) delete static_cast<SDCard*>(self);
    }

    int sdcard_disk_init(void* self) {
        return static_cast<SDCard*>(self)->mount() ? 0 : 1;
    }

    int sdcard_disk_read(void* self, uint8_t* buff, uint32_t sector, uint32_t count) {
        return (disk_read(self, buff, sector, count) == RES_OK) ? 0 : 1;
    }

    int sdcard_disk_write(void* self, const uint8_t* buff, uint32_t sector, uint32_t count) {
        return (disk_write(self, (BYTE*)buff, sector, count) == RES_OK) ? 0 : 1;
    }
}