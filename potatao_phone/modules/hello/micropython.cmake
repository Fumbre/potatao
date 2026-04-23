add_library(usermod_hello INTERFACE)

target_sources(usermod_hello INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/hello.c
)

target_include_directories(usermod_hello INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod_hello INTERFACE
    usermod
)

# Register with MicroPython build system
target_link_libraries(usermod INTERFACE usermod_hello)