from machine import Pin, I2C
import time

print("=" * 40)
print("  POTATAO — I2C Display Scan Tool")
print("=" * 40)
print()

# All valid I2C pin combinations for the Pico 2W
# Format: (bus_id, sda_pin, scl_pin)
CONFIGS = [
    (0, 0,  1),
    (0, 4,  5),
    (0, 8,  9),
    (0, 12, 13),
    (0, 16, 17),
    (0, 20, 21),
    (1, 2,  3),
    (1, 6,  7),
    (1, 10, 11),
    (1, 14, 15),
    (1, 18, 19),
    (1, 26, 27),
]

found_any = False

for bus, sda, scl in CONFIGS:
    try:
        print(f"Testing I2C{bus}: SDA=GP{sda:<2}  SCL=GP{scl:<2} ...", end=" ")
        i2c = I2C(bus, sda=Pin(sda), scl=Pin(scl), freq=100_000)
        devices = i2c.scan()

        if devices:
            found_any = True
            addrs = [hex(d) for d in devices]
            print(f"FOUND {len(devices)} device(s): {addrs}")
            # Identify known display addresses
            for d in devices:
                if d == 0x3C:
                    print(f"  >> 0x3C = SSD1306 OLED display (standard address)")
                elif d == 0x3D:
                    print(f"  >> 0x3D = SSD1306 OLED display (alternate address)")
                else:
                    print(f"  >> {hex(d)} = unknown device")
        else:
            print("no devices")

    except Exception as e:
        print(f"ERROR: {e}")

    time.sleep_ms(50)

print()
print("=" * 40)
if found_any:
    print("  Scan complete: device(s) found!")
    print("  Use the pins shown above in oled_ui.py")
else:
    print("  Scan complete: nothing found.")
    print("  Check wiring or try a different module.")
print("=" * 40)
