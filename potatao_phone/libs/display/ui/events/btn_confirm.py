# libs/display/ui/events/btn_confirm.py

from libs.display.ui.Views.main_view      import MainView
from libs.display.ui.Views.settings_view  import SettingsView
from libs.display.ui.Views.room_view      import RoomView

# map screen name → view class
VIEW_MAP = {
    "MAIN":      MainView,
    "SETTINGS":  SettingsView,
    "ROOM_VIEW": RoomView,
}

def handle(state):
    """called when agree/confirm button pressed"""
    if state.is_recording:
        return

    screen = state.current_screen()
    cursor = state.cursor()
    view   = VIEW_MAP.get(screen)

    if not view:
        return

    item  = view.selected_item(cursor)
    route = view.selected_route(cursor)

    # None route = special action
    if route is None:
        _handle_special(state, screen, item, cursor)
        return

    # build context for next screen
    ctx = dict(state.current_context())   # carry existing context forward
    ctx["from"]  = screen                 # know where we came from
    ctx["item"]  = item                   # what was selected

    # room-specific context
    if screen == "MAIN":
        ctx["room"] = item

    # push next screen and init it
    next_view = VIEW_MAP.get(route)
    if next_view:
        next_view.init()   # let view fetch its data

    state.push(route, ctx)
    state.reset_cursor()


def _handle_special(state, screen, item, cursor):
    """handles None routes — Back, special actions"""
    if item == "Back":
        state.pop()
    elif item == "Record":
        state.is_recording = True
        state.push("RECORDING", state.current_context())