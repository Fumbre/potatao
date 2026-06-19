from machine import SPI, Pin
import os

SDCARD_PIN_CS   = 13
SDCARD_PIN_CLK  = 14
SDCARD_PIN_MOSI = 15
SDCARD_PIN_MISO = 12

def test_sdcard():
    print("Initializing SPI...")
    spi = SPI(1,
        baudrate=1_000_000,
        polarity=0,
        phase=0,
        sck=Pin(SDCARD_PIN_CLK),
        mosi=Pin(SDCARD_PIN_MOSI),
        miso=Pin(SDCARD_PIN_MISO)
    )

    print("Initializing SD card...")
    try:
        import sdcard
        sd = sdcard.SDCard(spi, Pin(SDCARD_PIN_CS))
        print("✅ SD card detected!")
    except Exception as e:
        print("❌ SD card init failed:", e)
        return

    print("Mounting filesystem...")
    try:
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        print("✅ Mounted at /sd")
    except Exception as e:
        print("❌ Mount failed:", e)
        return

    print("Listing /sd:")
    for f in os.listdir("/sd"):
        print("  ", f)

    print("Writing test file...")
    try:
        with open("/sd/test.txt", "w") as f:
            f.write("hello from pico!")
        print("✅ Write OK!")
    except Exception as e:
        print("❌ Write failed:", e)
        return

    print("Reading test file...")
    with open("/sd/test.txt", "r") as f:
        print("✅ Read:", f.read())

    os.umount("/sd")
    print("✅ All done!")

test_sdcard()
