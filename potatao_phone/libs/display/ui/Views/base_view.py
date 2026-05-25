# libs/display/ui/Views/base_view.py

class BaseView:
    SCREEN_NAME = "Potatao"
    items       = []
    routes      = []   # same index as items

    @classmethod
    def init(cls):
        """called when view is pushed — fetch data, reset state"""
        pass

    @classmethod
    def render(cls, ui, cursor):
        raise NotImplementedError

    @classmethod
    def item_count(cls) -> int:
        return len(cls.items)

    @classmethod
    def selected_item(cls, cursor) -> str:
        if cls.items and cursor < len(cls.items):
            return cls.items[cursor]
        return ""

    @classmethod
    def selected_route(cls, cursor) -> str:
        if cls.routes and cursor < len(cls.routes):
            return cls.routes[cursor]
        return ""