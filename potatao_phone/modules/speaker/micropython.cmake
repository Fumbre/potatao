# Define the Speaker module interface
add_library(usermod_speaker INTERFACE)

# Target the source file
target_sources(usermod_speaker INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/speaker.c
)

# 🌟 FIX THE COMPILATION ORDER BUG:
# We explicitly force the build pipeline to generate the PIO headers
# for 'pico_audio_i2s' before attempting to compile speaker.c
target_link_libraries(usermod_speaker INTERFACE 
    pico_audio_i2s
    hardware_pio
)

# Connect back into the core user module assembly pipelines
target_link_libraries(usermod INTERFACE usermod_speaker)