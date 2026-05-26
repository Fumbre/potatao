add_library(usermod_jwt INTERFACE)

target_sources(usermod_jwt INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/jwt.c
)

target_include_directories(usermod_jwt INTERFACE
    ${MICROPY_DIR}/lib/pico-sdk/lib/mbedtls/include
)

target_link_libraries(usermod INTERFACE usermod_jwt)