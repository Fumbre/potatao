# Reusable UI library for the SSD1306 128x64 OLED display.
# Provides common screen patterns: splash, menu, status HUD, notifications.
#
# Wiring (I2C bus 1, avoids conflict with I2S mic on bus 0):
#   GP2  -> SDA
#   GP3  -> SCL
#   3.3V -> VCC
#   GND  -> GND

from machine import Pin, SoftI2C
from libs.display.oled import sh1106
import time

from import 

# Screen width in pixels
WIDTH  = 128

# Screen height in pixels
HEIGHT = 64

# Height of each text row: 8px character + 2px gap between lines
LINE_H = 10


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

    def __init__(self, sda_pin=10, scl_pin=11, freq=50_000):
        """
        @name        __init__
        @authors     Francisco
        @date        07-05-2026
        @details     Initialises the OLED display over I2C. Automatically
                     detects the I2C address (0x3C on most modules, 0x3D
                     on some). Raises RuntimeError if no display is found.
        @param       sda_pin   GPIO pin number for SDA (default: 10)
        @param       scl_pin   GPIO pin number for SCL (default: 11)
        @param       freq      I2C clock frequency in Hz (default: 50000)
        """

        # Creates the software I2C bus on the given pins and frequency
        i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)

        # Scans the I2C bus and returns a list of addresses of all found devices
        devices = i2c.scan()

        # If the list is empty, no device was found on the bus
        if not devices:
            # Raise an error immediately — no point continuing without a screen
            raise RuntimeError("No I2C device found. Check wiring!")

        # Take the address of the first found device (usually 0x3C)
        addr = devices[0]

        # Print the address in hexadecimal to the terminal for debugging
        print(f"OLED found at I2C address: 0x{addr:02X}")

        # Create the SH1106 driver object with the resolution, I2C bus and address
        self.oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=addr)

        # Call clear() to initialise the screen as soon as the object is created
        self.clear()

    def clear(self):
        # Iterates over every pixel row (0 to 63)
        for y in range(HEIGHT):
            # For each row, iterates over every column (0 to 127)
            for x in range(WIDTH):
                # Turns on the pixel at position (x, y) to white (1)
                # NOTE: despite being called "clear", this fills the screen WHITE
                # The inverted behaviour may be intentional for the SH1106 display
                self.oled.pixel(x, y, 1)

        # Pushes the buffer to the physical screen — without this, nothing is visible
        self.oled.show()

    def show(self):
        """
        @name        show
        @authors     Francisco
        @date        07-05-2026
        @details     Pushes the current frame buffer to the physical display.
                     Call after any manual drawing operations.
        """

        # Pushes the current buffer to the screen — convenience method for external use
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

        # Calls the driver's text method, converting msg to str
        # The conversion ensures compatibility even if a number is passed in
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

        # Clears the entire screen (all pixels to black)
        self.oled.fill(0)

        # Calculates x to horizontally centre the title
        # Each character is 8px wide: (128 - num_chars × 8) ÷ 2
        x = (WIDTH - len(title) * 8) // 2

        # Draws the title centred at y=18
        self.oled.text(title, x, 18, 1)

        # Calculates x to horizontally centre the subtitle using the same formula
        x2 = (WIDTH - len(subtitle) * 8) // 2

        # Draws the subtitle centred at y=34
        self.oled.text(subtitle, x2, 34, 1)

        # Draws a horizontal line spanning the full width at y=56
        self.oled.hline(0, 56, WIDTH, 1)

        # Writes the institution name at the bottom at x=24, y=58
        self.oled.text("NHL Stenden", 24, 58, 1)

        # Pushes everything to the physical screen
        self.oled.show()

        # Blocks the program for `duration` seconds
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

        # Clears the screen
        self.oled.fill(0)

        # Number of rows reserved for the title (0 if there is no title)
        row_offset = 0

        # Checks if a title was passed
        if title:
            # Draws the title in the top-left corner
            self.oled.text(title, 0, 0, 1)

            # Draws a separator line below the title at y=9
            self.oled.hline(0, 9, WIDTH, 1)

            # Reserves 1 row for the title so items start below it
            row_offset = 1

        # Calculates how many item rows fit on screen: 64 ÷ 10 = 6, minus the title offset
        visible_rows = (HEIGHT // LINE_H) - row_offset

        # Calculates the scroll offset needed to keep the selected item visible
        # max(0, ...) ensures scroll never goes negative (can't scroll above the top)
        scroll = max(0, selected - visible_rows + 1)

        # Iterates only over the items visible in the current window
        # items[scroll : scroll + visible_rows] is the "window" of visible items
        for i, item in enumerate(items[scroll : scroll + visible_rows]):

            # Absolute index in the full list (relative index + scroll offset)
            abs_i = i + scroll

            # Pixel y position for this item
            y = (i + row_offset) * LINE_H

            # Checks if this is the currently selected item
            if abs_i == selected:
                # Fills a white rectangle across the full width on this row (inverted background)
                self.oled.fill_rect(0, y, WIDTH, LINE_H, 1)

                # Draws the text with ">" in black (color=0) on the white background
                # [:16] clips to 16 characters to avoid overflowing off the screen
                self.oled.text(f"> {item}"[:16], 0, y + 1, 0)

            else:
                # Normal item: white text on black background
                # Two leading spaces to align with the "> " of the selected item
                self.oled.text(f"  {item}"[:16], 0, y + 1, 1)

        # Pushes the complete menu to the screen
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

        # Clears the screen
        self.oled.fill(0)

        # Fills the top bar (y=0 to y=10) with white (inverted background)
        self.oled.fill_rect(0, 0, WIDTH, 10, 1)

        # Determines the status text depending on whether recording is active
        status = "REC" if recording else "IDLE"

        # Writes the channel and status in BLACK (color=0) on the white top bar, at x=2, y=1
        self.oled.text(f"CH:{channel}  {status}", 2, 1, 0)

        # Writes the selected language in the body at y=14
        self.oled.text(f"Lang: {lang}", 0, 14, 1)

        # Writes the number of received messages at y=26
        self.oled.text(f"Msgs: {msg_count}", 0, 26, 1)

        # Draws a separator line at the bottom at y=54
        self.oled.hline(0, 54, WIDTH, 1)

        # Writes the button hints below the separator line at y=56
        self.oled.text("UP/DN=menu SEL=rec", 0, 56, 1)

        # Pushes everything to the screen
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

        # Clears the screen
        self.oled.fill(0)

        # Draws a border (outline only, no fill) around the entire screen
        self.oled.rect(0, 0, WIDTH, HEIGHT, 1)

        # Calculates x to centre line 1
        # max(0, ...) prevents negative values if the text is too long
        x1 = max(0, (WIDTH - len(line1) * 8) // 2)

        # Draws the first line centred at y=20, clipped to 16 characters
        self.oled.text(line1[:16], x1, 20, 1)

        # Checks if a second line was passed
        if line2:
            # Calculates x to centre line 2
            x2 = max(0, (WIDTH - len(line2) * 8) // 2)

            # Draws the second line centred at y=34, clipped to 16 characters
            self.oled.text(line2[:16], x2, 34, 1)

        # Pushes the popup to the screen
        self.oled.show()

        # Blocks for `duration` seconds
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

        # Clears the screen
        self.oled.fill(0)

        # Draws the label at y=10, clipped to 16 characters
        self.oled.text(label[:16], 0, 10, 1)

        # Calculates the filled width proportional to the percentage
        # WIDTH - 4 = 124px is the maximum bar width (2px margin on each side)
        bar_w = int((WIDTH - 4) * percent / 100)

        # Draws the bar outline: starts at x=2, y=30, with 124px width and 12px height
        self.oled.rect(2, 30, WIDTH - 4, 12, 1)

        # Fills the proportional part of the bar with the calculated width
        self.oled.fill_rect(2, 30, bar_w, 12, 1)

        # Writes the percentage as text, approximately centred at x=54, y=50
        self.oled.text(f"{percent}%", 54, 50, 1)

        # Pushes everything to the screen
        self.oled.show()
    
    def draw_screen(self, ui_view):
        if ui_view == 'wifi_room':
            print('cool')
            

