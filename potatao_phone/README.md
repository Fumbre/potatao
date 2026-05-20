# potatao phone

## FRESH START
git submodule update --init --recursivesudo pacman -S arm-none-eabi-gcc arm-none-eabi-gdb arm-none-eabi-binutils cmake make libusb

## Build
./build_build_micropython

## Files that should be on Pico

1. folder: libs
2. file: .env
3. main.py

## Native SD card module

The firmware includes a native MicroPython module named `sdcard`.

```python
from machine import SPI, Pin
import os
import sdcard

spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
os.mount(os.VfsFat(sd), "/sd")
```


## debugging mode

mention: Raspberry pi debug probe just only debug your cutomized C code which is customized micropython.ut2.

tips: if you want to test your customized C code. Firstly you need upload your testing python code to pico, and use proba to debug. Because openOCD will occupies your serial port, you can't open micropython terminal at the same time

1. install required libraries in your OS

   sudo pacman -S arm-none-eabi-gcc arm-none-eabi-gdb arm-none-eabi-binutils cmake make libusb
   sudo pacman -S git autoconf automake libtool libusb pkg-config make gcc
   sudo pacman -S jimtcl pkgconf

2. compile Raspberry pi openOCD
   
   (1) cd ./tools/openocd

   (2) ./bootstrap

   (3) ./configure --enable-cmsis-dap or ./configure --disable-werror

   (4) make -j$(nproc)

   (5) ./src/openocd --version   (just confirm whether openocd compiles successfully. result exmaple: Open On-Chip Debugger 0.12.0+dev-gacff23f)

3. remake custom micropython.uf2
   
   cd ~/your own path/potatao/potatao_phone

   ./build_micropython.sh debug  (without debug argument, it's release version)

4. upload customized micropython.ut2 to your pico 
   
   (1) boostel your pico

   (2) sudo mount /dev/your pico /mnt/pico
   
   (3) sudo cp ./your customized mictropython.uf2 /mnt/pico && sync

5. create launch.json file

   (1) cd ~/your project path/potatao/potatao_phone

   (2) mkdir .vscode (if you don't have this folder) 

   (3) create launch.json

   (4) copy this context below into your launch.json file

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Pico 2 W Debug",
            "type": "cortex-debug",
            "request": "launch",
            "servertype": "openocd",
            "cwd": "${workspaceRoot}",
            "executable": "${workspaceRoot}/build/micropython-rp2-pico2_w/firmware.elf",
            "serverpath": "${workspaceRoot}/tools/openocd/src/openocd",
            "configFiles": [
                "interface/cmsis-dap.cfg",
                "target/rp2350.cfg"
            ],
            "searchDir": [
                "${workspaceRoot}/tools/openocd/tcl",
                "${workspaceRoot}/tools/openocd/tcl/interface",
                "${workspaceRoot}/tools/openocd/tcl/target"
            ],
            "openOCDLaunchCommands": [
                "adapter speed 5000"
            ],
            "svdFile": "${env:PICO_SDK_PATH}/src/rp2350/hardware_regs/rp2350.svd",
            "runToEntryPoint": "main",
            "gdbPath": "arm-none-eabi-gdb"
        }
    ]
}
```

   (5) Press F5. it will be work.
