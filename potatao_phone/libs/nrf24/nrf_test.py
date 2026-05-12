from machine import Pin, SPI
import time
import struct
from libs.nrf24.nrf24l01 import NRF24L01

csn = Pin(14, mode=Pin.OUT, value=1)  # Chip Select Not pin
ce = Pin(17, mode=Pin.OUT, value=0)   # Chip
payload_size = 20 # Set the payload size (max 32 bytes for nRF24L01)


role = "send" # Change to "send" for the sender device

if role == "receive":
    send_pipe = b"\xe1\xf0\xf0\xf0\xf0" # Must match the sender's address
    receive_pipe = b"\xd2\xf0\xf0\xf0\xf0" # Must match the sender's address
else:
    send_pipe = b"\xd2\xf0\xf0\xf0\xf0"
    receive_pipe = b"\xe1\xf0\xf0\xf0\xf0"

def setup():
    spi = SPI(0,
          sck=Pin(6),
          mosi=Pin(7),
          miso=Pin(4),
          baudrate=1000000)

    print("Init nrf24 module")
    nrf = NRF24L01(spi, csn, ce, payload_size=payload_size)
    nrf.open_tx_pipe(send_pipe)
    nrf.open_rx_pipe(1, receive_pipe)
    nrf.start_listening()
    return nrf

def send(nrf, msg):
    print("sending message.", msg)
    nrf.stop_listening()  # Stop listening to send
    for n in range(len(msg)):
        try:
            encoded_string= msg[n].encode()
            byte_array = bytearray(encoded_string)
            buf = struct.pack('s', byte_array)  # Pad to 20 byte
            nrf.send(buf)
            print(role,"message", msg[n], "sent")
        except OSError:
            print(role,"Sorry message not sent")
    nrf.send("\n")
    nrf.start_listening()

nrf = setup()
nrf.start_listening()
msg_string = ""

while True:
    msg = ""
    if role == "send":
        send(nrf, "Hello world")
        send(nrf, "Test")
    else:
        if nrf.any():
            package = nrf.recv()
            message = struct.unpack("s",package)
            msg = message[0].decode()

            if (msg == "\n") and (len(msg_string) <= 20):
                print("full message", msg_string, msg)
                msg_string = ""
            else:
                if len(msg_string) <= 20:
                    msg_string = msg_string + msg
                else:
                    msg_string
