# libs/display/ui/Views/Rooms/rooms_view.py
from libs.display.ui.Views.base_view import BaseView

class MainView(BaseView):
    SCREEN_NAME = "Rooms list"

    # populated from backend after wifi connects
    items  = ["Test1", "Test2"]
    routes = ["", ""]

    @classmethod
    def init(cls):
        """in future: fetch rooms from backend here"""
        pass

    @classmethod
    def set_items(cls, items: list, routes: list):
        """called after backend responds"""
        cls.items  = list(items)
        cls.routes = list(routes)

    @classmethod
    def render(cls, ui, cursor):
        ui.render_header("Potatao", inverted=True)
        ui.render_main(cls.items, cursor)
        ui.render_footer("ENC=nav OK=enter")