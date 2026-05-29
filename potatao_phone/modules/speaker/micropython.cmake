# Define the Speaker module interface
add_library(usermod_speaker INTERFACE)

# Target the source file
target_sources(usermod_speaker INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/speaker.c
)

# -----------------------------------------------------------------------------
# ✅ PROPER PIO GENERATION FIX
# Compiles the real audio_i2s.pio into a proper header
# instead of injecting dummy instructions that break CYW43 Wi-Fi
# -----------------------------------------------------------------------------
set(AUDIO_I2S_PIO_SRC "${PICO_EXTRAS_PATH}/src/rp2_common/pico_audio_i2s/audio_i2s.pio")
set(OUTPUT_PIO_DIR "${CMAKE_BINARY_DIR}/generated/audio_i2s")

if(EXISTS ${AUDIO_I2S_PIO_SRC})
    file(MAKE_DIRECTORY ${OUTPUT_PIO_DIR})

    # Find pioasm tool (comes with Pico SDK)
    find_program(PIOASM_TOOL pioasm
        HINTS
            ${PICO_SDK_PATH}/tools/pioasm
            ${CMAKE_BINARY_DIR}/pioasm
            ${CMAKE_BINARY_DIR}
        REQUIRED
    )

    message(STATUS "Potatao: Found pioasm at ${PIOASM_TOOL}")
    message(STATUS "Potatao: Compiling real audio_i2s.pio → audio_i2s.pio.h")

    # Run pioasm at configure time to generate the real header
    execute_process(
        COMMAND ${PIOASM_TOOL} ${AUDIO_I2S_PIO_SRC} ${OUTPUT_PIO_DIR}/audio_i2s.pio.h
        RESULT_VARIABLE PIOASM_RESULT
        OUTPUT_VARIABLE PIOASM_OUTPUT
        ERROR_VARIABLE  PIOASM_ERROR
    )

    if(NOT PIOASM_RESULT EQUAL 0)
        message(FATAL_ERROR "pioasm failed to compile audio_i2s.pio:\n${PIOASM_ERROR}")
    else()
        message(STATUS "Potatao: audio_i2s.pio.h generated successfully ✅")
    endif()

    # Expose the generated header to the speaker module and usermod
    target_include_directories(usermod_speaker INTERFACE ${OUTPUT_PIO_DIR})
    target_include_directories(usermod INTERFACE ${OUTPUT_PIO_DIR})

else()
    message(FATAL_ERROR "Could not find audio_i2s.pio at: ${AUDIO_I2S_PIO_SRC}")
endif()

# Link hardware libraries
target_link_libraries(usermod_speaker INTERFACE
    pico_audio
    pico_audio_i2s
    hardware_pio
)

# Connect back into the core user module assembly pipelines
target_link_libraries(usermod INTERFACE usermod_speaker)