import gc


# Force a garbage collection so we get a clean baseline
gc.collect()
mem_before = gc.mem_free()


mem_after = gc.mem_free()
print(f"MicroPython RAM used by query: {mem_before - mem_after} bytes")
print(f"Total Free MicroPython RAM: {mem_after} bytes")
