import network
from libs.wifi.wifi import Wifi
import socket
import time
import os
from machine import SPI, Pin
import sdcard
from libs.conf.env import load_env

config = load_env()
SSID = config.get("SSID", "")
WIFI_PASSWORD = config.get("WIFI_PASSWORD", "")
SERVER_IP = config.get("SERVER_IP", "")

# --- SETTINGS ---
def setup():
    global wifi
    wifi = Wifi(SSID, WIFI_PASSWORD)
setup()

wifi.connect()

DEST_PORT = 5005
FILE_PATH = "/sd/test_record.wav"

# --- SD INITIALIZATION ---
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
os.mount(os.VfsFat(sd), "/sd")

# --- UDP SETUP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_file():
    try:
        stats = os.stat(FILE_PATH)
        file_size = stats[6]
        print(f"Sending {FILE_PATH} ({file_size} bytes)...")
        
        with open(FILE_PATH, "rb") as f:
            # Skip the first 44 bytes (the WAV header) 
            # because your PC script creates a NEW header automatically
            f.seek(44) 
            
            bytes_sent = 0
            while True:
                chunk = f.read(1024) # Match the buffer size of your PC script
                if not chunk:
                    break
                
                sock.sendto(chunk, (SERVER_IP, DEST_PORT))
                bytes_sent += len(chunk)
                
                # Small delay to avoid overwhelming the UDP stack
                time.sleep_ms(5) 
                
                if (bytes_sent // 1024) % 10 == 0:
                    print(f"Sent {bytes_sent}/{file_size} bytes", end='\r')

        print("\n✅ Transfer Complete!")
    except Exception as e:
        print("\n❌ Error:", e)
        os.umount("/sd")
    finally:
        sock.close()
        os.umount("/sd")

# Run the transfer
send_file()
