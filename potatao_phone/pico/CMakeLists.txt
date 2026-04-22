add_executable(potatao
    main.cpp
)

target_include_directories(potatao PRIVATE
    ../lib        # so main.cpp can write #include "audio/audio.h"
    ../modules    # so main.cpp can write #include "speaker/speaker.h"
)

target_link_libraries(potatao
    pico_stdlib
    audio
    speaker
)

# pico_add_extra_outputs(potatao)
pico_add_uf2_output(potatao)   # only uf2 as we decided earlier

add_custom_command(TARGET potatao POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_CURRENT_BINARY_DIR}/potatao.uf2
        ${CMAKE_BINARY_DIR}/potatao_phone.uf2
    COMMENT "Copying potatao_phone.uf2 to build root"
)