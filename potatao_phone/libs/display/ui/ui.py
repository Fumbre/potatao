from machine import Pin, I2C
from libs.display.oled import sh1106
from libs.conf.pins import PIN_OLED_SDA, PIN_OLED_SCL

WIDTH  = 128
HEIGHT = 64
LINE_H = 10

# zone boundaries
ZONE_TOP_H     = 10   # y=0  to y=10
ZONE_CONTENT_Y = 10   # y=10 to y=54
ZONE_CONTENT_H = 44
ZONE_BOTTOM_Y  = 54   # y=54 to y=64
ZONE_BOTTOM_H  = 10

class UI:
    def __init__(self, sda_pin=PIN_OLED_SDA, scl_pin=PIN_OLED_SCL, freq=400_000):
        # use hardware I2C not SoftI2C — faster, less CPU
        i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found. Check wiring!")
        self.oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=devices[0])
        self.oled.fill(0)
        self.oled.show()

    # ── ZONE RENDERING ──────────────────────────────────

    def render_header(self, text, inverted=False):
        """renders header bar — call only when top content changes"""
        bg = 1 if inverted else 0
        fg = 0 if inverted else 1
        self.oled.fill_rect(0, 0, WIDTH, ZONE_TOP_H, bg)
        self.oled.text(text[:16], 2, 1, fg)

    def render_main(self, items, selected, scroll=0):
        """renders main zone only — call when cursor moves"""
        self.oled.fill_rect(0, ZONE_CONTENT_Y, WIDTH, ZONE_CONTENT_H, 0)
        visible = ZONE_CONTENT_H // LINE_H   # 4 rows visible

        for i, item in enumerate(items[scroll: scroll + visible]):
            abs_i = i + scroll
            y = ZONE_CONTENT_Y + (i * LINE_H)
            if abs_i == selected:
                self.oled.fill_rect(0, y, WIDTH, LINE_H, 1)
                self.oled.text(f"> {item}"[:16], 0, y + 1, 0)
            else:
                self.oled.text(f"  {item}"[:16], 0, y + 1, 1)

    def render_footer(self, text):
        """renders footer hint bar — call only when hints change"""
        self.oled.fill_rect(0, ZONE_BOTTOM_Y, WIDTH, ZONE_BOTTOM_H, 0)
        self.oled.hline(0, ZONE_BOTTOM_Y, WIDTH, 1)
        self.oled.text(text[:16], 0, ZONE_BOTTOM_Y + 2, 1)

    def flush(self):
        """push buffer to screen — call ONCE after all zones rendered"""
        self.oled.show()

    # ── FULL SCREEN HELPERS ─────────────────────────────

    def splash(self, title="POTATAO", subtitle="Loading..."):
        self.oled.fill(0)
        x = (WIDTH - len(title) * 8) // 2
        self.oled.text(title, x, 18, 1)
        x2 = (WIDTH - len(subtitle) * 8) // 2
        self.oled.text(subtitle, x2, 34, 1)
        self.oled.hline(0, 56, WIDTH, 1)
        self.oled.text("NHL Stenden", 24, 58, 1)
        self.oled.show()

    # notify can use footer (mb header) notification
    def notify(self, line1, line2=""):
        self.oled.fill(0)
        self.oled.rect(0, 0, WIDTH, HEIGHT, 1)
        x1 = max(0, (WIDTH - len(line1) * 8) // 2)
        self.oled.text(line1[:16], x1, 20, 1)
        if line2:
            x2 = max(0, (WIDTH - len(line2) * 8) // 2)
            self.oled.text(line2[:16], x2, 34, 1)
        self.oled.show()