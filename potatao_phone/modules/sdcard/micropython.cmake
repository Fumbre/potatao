# Define the user module library
add_library(usermod_sdcard INTERFACE)

# Add the C source file to the module
target_sources(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sdcard.c
)

# Include the current directory for header lookup
target_include_directories(usermod_sdcard INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# Generate the pio.h header from the .pio file
# This is required for the Pico 2 W (RP2350) PIO hardware
if (COMMAND pico_generate_pio_header)
    pico_generate_pio_header(usermod_sdcard ${CMAKE_CURRENT_LIST_DIR}/sdcard.pio)
endif()

# Link required Pico SDK hardware libraries
# hardware_pio: Essential for the SD card state machine
# hardware_clocks: Required for calculating baudrate on the 150MHz RP2350
target_link_libraries(usermod_sdcard INTERFACE
    hardware_pio
    hardware_clocks
)

# Register the module to the MicroPython build system
target_link_libraries(usermod INTERFACE usermod_sdcard)