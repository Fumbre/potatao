enable_language(ASM)

add_library(usermod_x25519 INTERFACE)

target_sources(usermod_x25519 INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/x25519.c
    ${CMAKE_CURRENT_LIST_DIR}/x25519-cm0.S
)

set_source_files_properties(
    ${CMAKE_CURRENT_LIST_DIR}/x25519-cm0.S
    PROPERTIES LANGUAGE ASM
)

target_include_directories(usermod_x25519 INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_x25519)