# Potatao

This is university project 

We built here the complete structure for IoT device (RP pico 2w), statation that represents the remote pc (in our case we use RP zero 2w) and llm (remote local server) that translate the audio based on rp pico 2w (potatao_phone) preferened language settings.

The full reperesentation of all strucre and code that we need for potatao phone device and its server RP zero

## Potatao_phone
We've created a custom micropython firmware for our device. 

It include:
- OLED display (fronted part, represents menu and functionality)
- Sd Card (for UI database, and user storage )
- Mic (for audio)
- Speaker (allows listen audio)
- WiFi (for sending audio)
- Nrf radio module (also for sending audio if wifi is not connected)


### Programms requirements to build our custom micropython_potatao.uf2


#### Linux

- cmake
- arm-none-eabi (arm-none-eabi-gcc arm-none-eabi-newlib)
- uv (curl -LsSf https://astral.sh/uv/install.sh | sh)


#### MacOS
- brew install coreutils
brew tap armmbed/formulae
brew install arm-none-eabi-gcc cmake


The hardware part of potatao device 
includes hardware connectection & code implementation

We use mpremote for communication with pico 2w
Requiers files on Pico 2w (potatao_phone)
copy:
- mpremote mkdir libs
- mpremote cp -r libs/* :libs
- mpremote cp .env :.env
- mpremote cp main.py :main.py
- mpremote run main.py

#### start
0. git submodule update --init --recursive
1. cd potatao_phone/micropython
1.1  make -C mpy-cross

## Potatao_station
This is our remote server, python backend application
we build communication functionality with pico 2w (potatao_phone)
We have end to end encryption
We use websockets to transmit audio data by streaming (WiFi)
We also have minio to store those audio files using AWS3 protocal 

Pico registery function

### Future ideas
Pico monitoring funciton
Chatting room API

### Start Install

Install uv, redis, minio(2024)

#### Linux
sudo pacman -S uv

#### MacOS
brew install uv 

----------------------
install project libs

- uv sync --all-packages
