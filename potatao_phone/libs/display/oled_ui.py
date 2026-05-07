# Reusable UI library for the SSD1306 128x64 OLED display.
# Provides common screen patterns: splash, menu, status HUD, notifications.
#
# Wiring (I2C bus 1, avoids conflict with I2S mic on bus 0):
#   GP2  -> SDA
#   GP3  -> SCL
#   3.3V -> VCC
#   GND  -> GND

from machine import Pin, SoftI2C
from libs.display import ssd1306
import time

# Display resolution constants
WIDTH  = 128   # pixels wide
HEIGHT = 64    # pixels tall
LINE_H = 10    # height of each text row (8px char + 2px gap)


class OledUI:
    """
    @name        OledUI
    @authors     Francisco
    @date        07-05-2026
    @details     Wrapper class for the SSD1306 128x64 OLED display.
                 Provides reusable UI patterns for the Potatao device:
                 splash screen, scrollable menu, status HUD, notifications,
                 and a progress bar. Uses I2C bus 1 (GP2/GP3) to avoid
                 conflicts with the I2S microphone on bus 0.
    """

    def __init__(self, sda_pin=2, scl_pin=3, freq=50_000):
        """
        @name        __init__
        @authors     Francisco
        @date        07-05-2026
        @details     Initialises the OLED display over I2C. Automatically
                     detects the I2C address (0x3C on most modules, 0x3D
                     on some). Raises RuntimeError if no display is found.
        @param       sda_pin   GPIO pin number for SDA (default: 2)
        @param       scl_pin   GPIO pin number for SCL (default: 3)
        @param       i2c_id    I2C bus ID to use (default: 1)
        @param       freq      I2C clock frequency in Hz (default: 400000)
        """
        # Set up the I2C bus with the given pins and frequency
        i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        # Scan the bus for connected devices
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found. Check wiring!")

        addr = devices[0]
        print(f"OLED found at I2C address: 0x{addr:02X}")

        # Create the SSD1306 driver instance
        self.oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=addr)
        self.oled.write_cmd(0xA1)
        self.oled.write_cmd(0xC8)
        self.oled.fill(1)
        self.oled.show()
        self.oled.fill(1)
        self.oled.show()

    def clear(self):
        for y in range(HEIGHT):
            for x in range(WIDTH):
                self.oled.pixel(x, y, 1)
        self.oled.show()

    def show(self):
        """
        @name        show
        @authors     Francisco
        @date        07-05-2026
        @details     Pushes the current frame buffer to the physical display.
                     Call after any manual drawing operations.
        """
        self.oled.show()

    def text(self, msg, x, y, color=1):
        """
        @name        text
        @authors     Francisco
        @date        07-05-2026
        @details     Draws a single string at the given pixel position.
        @param       msg    String to draw (converted automatically)
        @param       x      Horizontal pixel position from the left
        @param       y      Vertical pixel position from the top
        @param       color  1 = white (default), 0 = black
        """
        self.oled.text(str(msg), x, y, color)

    def splash(self, title="POTATAO", subtitle="Loading...", duration=2):
        """
        @name        splash
        @authors     Francisco
        @date        07-05-2026
        @details     Displays a boot screen with a centred title and subtitle.
                     A horizontal line and institution name are drawn at the
                     bottom. Blocks for `duration` seconds before returning.
        @param       title     Main title text shown in the centre (default: "POTATAO")
        @param       subtitle  Smaller text shown below the title (default: "Loading...")
        @param       duration  Time in seconds to display the screen (default: 2)
        """
        self.oled.fill(0)

        # Centre the title horizontally (each char is 8px wide)
        x = (WIDTH - len(title) * 8) // 2
        self.oled.text(title, x, 18, 1)

        # Centre the subtitle
        x2 = (WIDTH - len(subtitle) * 8) // 2
        self.oled.text(subtitle, x2, 34, 1)

        # Bottom decorative line and institution label
        self.oled.hline(0, 56, WIDTH, 1)
        self.oled.text("NHL Stenden", 24, 58, 1)

        self.oled.show()
        time.sleep(duration)

    def menu(self, items, selected=0, title=None):
        """
        @name        menu
        @authors     Francisco
        @date        07-05-2026
        @details     Renders a scrollable list menu. The selected item is
                     highlighted with an inverted bar. The list scrolls
                     automatically to keep the selected item visible.
                     An optional title is drawn above the list with a
                     separator line.
        @param       items     List of strings to display as menu options
        @param       selected  Index of the currently highlighted item (default: 0)
        @param       title     Optional header text drawn above the list (default: None)
        """
        self.oled.fill(0)

        row_offset = 0  # rows reserved for the title

        if title:
            self.oled.text(title, 0, 0, 1)
            self.oled.hline(0, 9, WIDTH, 1)  # separator line under title
            row_offset = 1

        # How many list items fit on screen at once
        visible_rows = (HEIGHT // LINE_H) - row_offset

        # Scroll offset: shift window so selected item stays visible
        scroll = max(0, selected - visible_rows + 1)

        for i, item in enumerate(items[scroll : scroll + visible_rows]):
            abs_i = i + scroll  # absolute index in the full list
            y = (i + row_offset) * LINE_H

            if abs_i == selected:
                # Highlighted: white background, black text
                self.oled.fill_rect(0, y, WIDTH, LINE_H, 1)
                self.oled.text(f"> {item}"[:16], 0, y + 1, 0)
            else:
                # Normal: black background, white text
                self.oled.text(f"  {item}"[:16], 0, y + 1, 1)

        self.oled.show()

    def status_screen(self, channel, lang, msg_count, recording=False):
        """
        @name        status_screen
        @authors     Francisco
        @date        07-05-2026
        @details     Renders the main HUD shown on the Home screen.
                     Top bar (inverted) shows the current channel and
                     recording state. Body shows selected language and
                     message count. Bottom bar shows button hints.
        @param       channel     Channel name string to display
        @param       lang        Language code or name to display (e.g. "EN")
        @param       msg_count   Number of messages received so far
        @param       recording   True shows "REC", False shows "IDLE" (default: False)
        """
        self.oled.fill(0)

        # Inverted top bar
        self.oled.fill_rect(0, 0, WIDTH, 10, 1)
        status = "REC" if recording else "IDLE"
        self.oled.text(f"CH:{channel}  {status}", 2, 1, 0)  # black text on white

        # Body
        self.oled.text(f"Lang: {lang}", 0, 14, 1)
        self.oled.text(f"Msgs: {msg_count}", 0, 26, 1)

        # Bottom hint bar
        self.oled.hline(0, 54, WIDTH, 1)
        self.oled.text("UP/DN=menu SEL=rec", 0, 56, 1)

        self.oled.show()

    def notify(self, line1, line2="", duration=2):
        """
        @name        notify
        @authors     Francisco
        @date        07-05-2026
        @details     Displays a full screen notification popup with a border.
                     Up to two lines of text are centred on the screen.
                     Blocks for `duration` seconds before returning.
        @param       line1     First line of text (max 16 chars displayed)
        @param       line2     Optional second line of text (default: "")
        @param       duration  Time in seconds to display the popup (default: 2)
        """
        self.oled.fill(0)
        self.oled.rect(0, 0, WIDTH, HEIGHT, 1)  # border

        # Centre line 1
        x1 = max(0, (WIDTH - len(line1) * 8) // 2)
        self.oled.text(line1[:16], x1, 20, 1)

        # Centre line 2 (optional)
        if line2:
            x2 = max(0, (WIDTH - len(line2) * 8) // 2)
            self.oled.text(line2[:16], x2, 34, 1)

        self.oled.show()
        time.sleep(duration)

    def progress_bar(self, label, percent):
        """
        @name        progress_bar
        @authors     Francisco
        @date        07-05-2026
        @details     Displays a horizontal progress bar with a label above
                     and a percentage value below. Useful for showing loading
                     or upload progress on the device.
        @param       label    Text label shown above the bar (max 16 chars)
        @param       percent  Fill level from 0 (empty) to 100 (full)
        """
        self.oled.fill(0)
        self.oled.text(label[:16], 0, 10, 1)

        # Calculate filled width proportional to percent
        bar_w = int((WIDTH - 4) * percent / 100)

        # Outer border of the bar
        self.oled.rect(2, 30, WIDTH - 4, 12, 1)

        # Filled portion
        self.oled.fill_rect(2, 30, bar_w, 12, 1)

        self.oled.text(f"{percent}%", 54, 50, 1)
        self.oled.show()

        