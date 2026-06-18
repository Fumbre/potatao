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



### Build & Compile the Custom Firmware Engine
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
