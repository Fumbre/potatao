#include "py/runtime.h"
#include "py/obj.h"

// Python: hello.say()
static mp_obj_t hello_say(void) {
    mp_print_str(&mp_plat_print, "Hello from C world in Python execution!\n");
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(hello_say_obj, hello_say);

// Module globals table
static const mp_rom_map_elem_t hello_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_hello) },
    { MP_ROM_QSTR(MP_QSTR_say),      MP_OBJ_FROM_PTR(&hello_say_obj) },
};
static MP_DEFINE_CONST_DICT(hello_module_globals, hello_module_globals_table);

// Module definition
const mp_obj_module_t hello_module = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&hello_module_globals,
};

// Register with MicroPython
MP_REGISTER_MODULE(MP_QSTR_hello, hello_module);