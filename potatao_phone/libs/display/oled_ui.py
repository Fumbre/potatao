from machine import Pin, I2C
from libs.display import ssd1306
import time

WIDTH  = 128
HEIGHT = 64
LINE_H = 10

class OledUI:
    def __init__(self, sda_pin=2, scl_pin=3, i2c_id=1, freq=400_000):
        i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)

        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found. Check wiring!")
        addr = devices[0]
        print(f"OLED found at I2C address: 0x{addr:02X}")

        self.oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=addr)
        self.clear()

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def show(self):
        self.oled.show()

    def text(self, msg, x, y, color=1):
        self.oled.text(str(msg), x, y, color)

    def splash(self, title="POTATAO", subtitle="Loading...", duration=2):
        self.oled.fill(0)
        x = (WIDTH - len(title) * 8) // 2
        self.oled.text(title, x, 18, 1)
        x2 = (WIDTH - len(subtitle) * 8) // 2
        self.oled.text(subtitle, x2, 34, 1)
        self.oled.hline(0, 56, WIDTH, 1)
        self.oled.text("NHL Stenden", 24, 58, 1)
        self.oled.show()
        time.sleep(duration)

    def menu(self, items, selected=0, title=None):
        self.oled.fill(0)
        row_offset = 0
        if title:
            self.oled.text(title, 0, 0, 1)
            self.oled.hline(0, 9, WIDTH, 1)
            row_offset = 1

        visible_rows = (HEIGHT // LINE_H) - row_offset
        scroll = max(0, selected - visible_rows + 1)

        for i, item in enumerate(items[scroll : scroll + visible_rows]):
            abs_i = i + scroll
            y = (i + row_offset) * LINE_H
            if abs_i == selected:
                self.oled.fill_rect(0, y, WIDTH, LINE_H, 1)
                self.oled.text(f"> {item}"[:16], 0, y + 1, 0)
            else:
                self.oled.text(f"  {item}"[:16], 0, y + 1, 1)

        self.oled.show()

    def status_screen(self, channel, lang, msg_count, recording=False):
        self.oled.fill(0)
        self.oled.fill_rect(0, 0, WIDTH, 10, 1)
        status = "REC" if recording else "IDLE"
        self.oled.text(f"CH:{channel}  {status}", 2, 1, 0)
        self.oled.text(f"Lang: {lang}", 0, 14, 1)
        self.oled.text(f"Msgs: {msg_count}", 0, 26, 1)
        self.oled.hline(0, 54, WIDTH, 1)
        self.oled.text("UP/DN=menu SEL=rec", 0, 56, 1)
        self.oled.show()

    def notify(self, line1, line2="", duration=2):
        self.oled.fill(0)
        self.oled.rect(0, 0, WIDTH, HEIGHT, 1)
        x1 = max(0, (WIDTH - len(line1) * 8) // 2)
        self.oled.text(line1[:16], x1, 20, 1)
        if line2:
            x2 = max(0, (WIDTH - len(line2) * 8) // 2)
            self.oled.text(line2[:16], x2, 34, 1)
        self.oled.show()
        time.sleep(duration)

    def progress_bar(self, label, percent):
        self.oled.fill(0)
        self.oled.text(label[:16], 0, 10, 1)
        bar_w = int((WIDTH - 4) * percent / 100)
        self.oled.rect(2, 30, WIDTH - 4, 12, 1)
        self.oled.fill_rect(2, 30, bar_w, 12, 1)
        self.oled.text(f"{percent}%", 54, 50, 1)
        self.oled.show()

