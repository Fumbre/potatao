# libs/display/ui/Views/main_view.py
from libs.display.ui.Views.base_view import BaseView

class MainView(BaseView):
    SCREEN_NAME = "Home :)"

    # populated from backend after wifi connects
    items  = ["WiFi Room", "Sd Card", "NRF Room", "Settings"]

    # MainView
    # ["WiFi Room", "Sd Card", "NRF Room", "Settings"]

    #SettingsView
    # ["volume", "receive audio in language", "nickname"]

    #"receive audio in language"
    # [from zero data]
    
    #RoomsView
    # [list of current view] fetch http 

    # sd CArd menu
    # ["my_audio1", "my_audio2"]
    routes = ["", ""]

    @classmethod
    def init(cls):
        """in future: fetch rooms from backend here"""
        pass

    @classmethod
    def render(cls, ui, cursor):
        ui.render_header(cls.SCREEN_NAME, inverted=True)
        ui.render_main(cls.items, cursor)
        ui.render_footer("ENC=nav OK=enter")