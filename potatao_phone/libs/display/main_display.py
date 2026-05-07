from libs.display.oled_ui import OledUI
from machine import Pin
import time

ui = OledUI(sda_pin=2, scl_pin=3)

button_up   = Pin(20, Pin.IN, Pin.PULL_UP)
button_sel  = Pin(21, Pin.IN, Pin.PULL_UP)
button_down = Pin(22, Pin.IN, Pin.PULL_UP)

DEBOUNCE_MS = 180
last_press  = 0

MAIN_MENU = ["Status", "Language", "Channel", "Settings", "About"]
LANGUAGES = ["English", "Dutch", "Spanish", "French", "Ukrainian"]
CHANNELS  = ["General", "Room 1", "Room 2", "Private"]

state = {
    "screen":   "home",
    "menu_sel":  0,
    "language":  0,
    "channel":   0,
    "recording": False,
    "msg_count": 0,
}

def draw():
    s = state["screen"]
    if s == "home":
        ui.status_screen(
            channel   = CHANNELS[state["channel"]],
            lang      = LANGUAGES[state["language"]][:3].upper(),
            msg_count = state["msg_count"],
            recording = state["recording"],
        )
    elif s == "main_menu":
        ui.menu(MAIN_MENU, selected=state["menu_sel"], title="Menu")
    elif s == "lang_menu":
        ui.menu(LANGUAGES, selected=state["menu_sel"], title="Language")
    elif s == "chan_menu":
        ui.menu(CHANNELS, selected=state["menu_sel"], title="Channel")
    elif s == "about":
        ui.oled.fill(0)
        ui.text("POTATAO v0.1", 8, 4)
        ui.text("NHL Stenden 26", 0, 16)
        ui.text("SEL = back", 20, 50)
        ui.show()

def handle_up():
    s = state["screen"]
    if s == "home":
        state["language"] = (state["language"] - 1) % len(LANGUAGES)
    elif s in ("main_menu", "lang_menu", "chan_menu"):
        lengths = {"main_menu": len(MAIN_MENU), "lang_menu": len(LANGUAGES), "chan_menu": len(CHANNELS)}
        state["menu_sel"] = (state["menu_sel"] - 1) % lengths[s]

def handle_down():
    s = state["screen"]
    if s == "home":
        state["language"] = (state["language"] + 1) % len(LANGUAGES)
    elif s in ("main_menu", "lang_menu", "chan_menu"):
        lengths = {"main_menu": len(MAIN_MENU), "lang_menu": len(LANGUAGES), "chan_menu": len(CHANNELS)}
        state["menu_sel"] = (state["menu_sel"] + 1) % lengths[s]

def handle_select():
    s = state["screen"]
    if s == "home":
        state["recording"] = not state["recording"]
        ui.notify("Recording..." if state["recording"] else "Stopped", duration=1)
    elif s == "main_menu":
        choice = MAIN_MENU[state["menu_sel"]]
        if choice == "Status":     state["screen"] = "home"
        elif choice == "Language": state["screen"] = "lang_menu"; state["menu_sel"] = state["language"]
        elif choice == "Channel":  state["screen"] = "chan_menu";  state["menu_sel"] = state["channel"]
        elif choice == "About":    state["screen"] = "about"
    elif s == "lang_menu":
        state["language"] = state["menu_sel"]
        ui.notify("Language set!", LANGUAGES[state["language"]], 1)
        state["screen"] = "main_menu"
    elif s == "chan_menu":
        state["channel"] = state["menu_sel"]
        ui.notify("Channel set!", CHANNELS[state["channel"]], 1)
        state["screen"] = "main_menu"
    elif s == "about":
        state["screen"] = "main_menu"

ui.splash("POTATAO", "Starting...")
draw()

while True:
    now = time.ticks_ms()
    if button_up.value() == 0:
        if time.ticks_diff(now, last_press) > DEBOUNCE_MS:
            handle_up()
            draw()
            last_press = now
        while button_up.value() == 0:
            time.sleep_ms(10)
    elif button_sel.value() == 0:
        if time.ticks_diff(now, last_press) > DEBOUNCE_MS:
            handle_select()
            draw()
            last_press = now
        while button_sel.value() == 0:
            time.sleep_ms(10)
    elif button_down.value() == 0:
        if time.ticks_diff(now, last_press) > DEBOUNCE_MS:
            handle_down()
            draw()
            last_press = now
        while button_down.value() == 0:
            time.sleep_ms(10)
    time.sleep_ms(20)
    