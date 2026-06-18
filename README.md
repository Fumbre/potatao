# Potatao 🥔

An independent, real-time cross-language audio messaging system built around a custom-compiled hardware/software ecosystem. 

Potatao is an end-to-end IoT communication platform developed by a team of Computer Science students at NHL Stenden University of Applied Sciences (2026). The project enables a handheld device ("Potatao Phone") to record high-quality voice messages in a user's native language, stream them wirelessly, and process them through a local LLM translation pipeline to achieve real-time, cross-language audio communication.

---

## 🏗️ System Architecture Overview

The system is decoupled into three primary operational layers:

1. **Potatao Phone (Raspberry Pi Pico 2W):** The client hardware running a custom-built MicroPython firmware runtime with low-level C modules for time-critical hardware tasks (e.g., 24kHz audio capture). It implements an innovative database-driven UI configuration layer using `usqlite`.
2. **Potatao Station (Base Station / RPi Zero 2W):** A robust Python backend server facilitating secure, end-to-end encrypted streaming over WebSockets. It handles local cloud object storage (MinIO via AWS S3 protocol) and client registry mapping.
3. **Potatao LLM (Translation Engine):** A dedicated, local AI server using `Faster-Whisper` for rapid speech-to-text transcribing and specialized `Ollama` pipeline architectures for context-aware translation.

---

## 📱 Potatao Phone: Embedded Implementation

The physical handheld prototype integrates a dense suite of peripherals directly onto the Pico 2W. To bypass standard performance barriers in microcontrollers, the device relies on a custom-architected hybrid firmware engine.

### ⚡ The C/MicroPython Performance Breakthrough
Initially, utilizing an all-Python stack caused severe performance bottlenecks. During real-time high-quality audio capture over I2S, high-frequency Python loop iterations introduced immense interpreter overhead, leading to critical packet loss. 

To solve this, **the sample-processing loops were entirely rewritten in native C**, leveraging the `pico-sdk` wrapped tightly into a custom MicroPython firmware build. This native C layer directly interacts with the hardware registers, yielding an **approximate 100x increase in execution speed**. This optimization successfully unlocked seamless, real-time streaming of **24kHz raw audio** arrays.

### 🗄️ Database-Driven UI & Three-Manager Application Framework
To protect time-sensitive background tasks (such as Wi-Fi data streaming or microphone capture) from being interrupted or slowed down by UI rendering overhead, the client application logic is entirely driven by a local database (`usqlite`). 

Every menu view, action node, or configuration path is mapped directly inside an SQLite database stored on the SD Card. The runtime evaluates this tree dynamically through a decoupled, asynchronous three-manager architecture loop running inside `main.py`:
* **Event Manager:** Captures low-overhead hardware button events utilizing Interrupt Request (IRQ) flags. A continuous `event_manager.process()` call inside the main execution loop catches triggered flags asynchronously.
* **State Manager:** Maintains active application contexts (e.g., setting state flags like `is_recording = True`) and dynamically maps static button interactions to different programmatic tasks depending on the active menu loaded from the database stack. Basic navigation events (e.g., "Cancel") are handled directly by popping active dictionary states off the navigation context list.
* **Function Manager:** Responsible for executing the underlying native hardware routines when a state transition requires operational processing rather than basic UI menu routing.

### 🎙️ Audio Output Routing & File Isolation
Building upon the system's low-level storage capabilities, the audio rendering pipeline has been fully abstracted to support dynamic data routing. This grants the device the flexibility to dynamically push raw audio byte vectors over NRF24L01 radio channels, stream them directly through Wi-Fi WebSockets, or parse them locally out to the integrated speaker. 

Furthermore, data pathways are securely separated at the file-system layer to align cleanly with the UI. The onboard SD card organizes file targets into a structured directory map, isolating recorded audio into a distinct `/recordings` directory and routing incoming translated payloads strictly into a `/received` folder.

---

## 🛠️ Installation & Getting Started

### Prerequisites

#### Linux (Arch/Debian)
```bash
sudo pacman -S cmake arm-none-eabi-gcc arm-none-eabi-newlib redis
# Install uv tool for fast dependency resolution
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

#### MacOs
brew install coreutils cmake uv redis
brew tap armmbed/formulae
brew install arm-none-eabi-gcc


### Potatao Phone -> Build & Compile the Custom Firmware Engine
in /potatao_phone folder

#### Initialize Submodules
git submodule update --init --recursive

#### Compile the Custom Potatao Firmware
./build_micropython.sh

upload custom build from /build/micropython_potatao.uf2 to your pico 2w

#### Flashing Files onto the Pico 2W Client
We utilize mpremote for swift file-system deployments over active device connections. Ensure the following specific file hierarchy structure is mirrored perfectly to the root directory layout:

mpremote mkdir libs
mpremote cp -r libs/* :libs
mpremote cp .env :.env
mpremote cp main.py :main.py
mpremote run main.py

### Potatao Station -> Launching Backend Server
Ensure MinIO and Redis instances are running in your backend environment. Navigate to the station root, synchronize dependencies with uv, and initialize the pipeline:

cd potatao_station
uv sync --all-packages
uv run main.py



## 🐛 Hardware Debugging Probe Guide

[!NOTE]
The Raspberry Pi Debug Probe strictly debugs your customized C code within the firmware.elf target container.

To test low-level C firmware modifications, you must first flash your target testing Python scripts to the Pico filesystem and use the hardware probe to evaluate register execution. Because OpenOCD exclusively locks the physical serial interfaces, you will not be able to interact via an active MicroPython REPL loop terminal concurrently.


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
