import network

class Wifi:
    
    def __init__(self, ssid, password):
        self.SSID     = ssid
        self.PASSWORD = password

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

        pass

    def connect(self):
        self.wlan.connect(self.SSID, self.PASSWORD)
        print("I'm connected with this IP: ",  self.wlan.ifconfig()[0])
