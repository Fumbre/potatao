# Potatao

The full reperesentation of all strucre and code that we need for potatao phone device and its server RP zero

## Potatao_phone

### Programms requirements

- cmake
- arm-none-eabi (arm-none-eabi-gcc arm-none-eabi-newlib)
- uv (curl -LsSf https://astral.sh/uv/install.sh | sh)


# MacOS
- brew install coreutils
brew tap armmbed/formulae
brew install arm-none-eabi-gcc cmake


The hardware part of potatao device 
includes hardware connectection & code implementation

### start
0. git submodule update --init --recursive
1. cd potatao_phone/micropython
1.1  make -C mpy-cross

## backend
Right now it uses microservices for connections to devcies 
