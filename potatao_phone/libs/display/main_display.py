from libs.display.oled_ui import OledUI

ui = OledUI(sda_pin=10, scl_pin=11)
ui.oled.fill(0)
ui.oled.text("Hello World!", 0, 0, 1)
ui.oled.show()

while True:
    pass