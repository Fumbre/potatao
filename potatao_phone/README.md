# potatao phone

## FRESH START
git submodule update --init --recursive


Mic, speaker, sd card

## start
mkdir build
cd build
cmake ..
make -j$(nproc)


- pinouts for speaker - 
vin - 36 3V3(OUT)
GND - 33
DIN - 6 GP4
LRC - 5 GP3
BCLK - 4 GP2