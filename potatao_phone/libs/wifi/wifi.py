import network
import time

class Wifi:
    def __init__(self, ssid, password):
        self.SSID     = ssid
        self.PASSWORD = password
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def connect(self, max_attempts=10, delay=2):
        print(f"Connecting to {self.SSID}...")

        # If already connected, skip
        if self.wlan.isconnected():
            print("Already connected:", self.wlan.ifconfig()[0])
            return True

        self.wlan.connect(self.SSID, self.PASSWORD)

        for attempt in range(max_attempts):
            status = self.wlan.status()

            if self.wlan.isconnected():
                print(f"✅ Connected! IP: {self.wlan.ifconfig()[0]}")
                return True

            # Check for permanent failures — no point retrying these
            if status == network.STAT_WRONG_PASSWORD:
                print("Wrong password!")
                return False
            if status == network.STAT_NO_AP_FOUND:
                print(f"Network '{self.SSID}' not found!")
                return False

            print(f"   Waiting... attempt {attempt + 1}/{max_attempts} (status={status})")
            time.sleep(delay)

        # If we get here — timed out, try full reconnect
        print("Timed out, retrying full reconnect...")
        self.wlan.disconnect()
        time.sleep(1)
        return self.connect(max_attempts, delay)  # recursive retry

    def is_connected(self):
        return self.wlan.isconnected()

    def ip(self):
        return self.wlan.ifconfig()[0]

    def disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)
        print("Disconnected")
        