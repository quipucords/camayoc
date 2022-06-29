from .components.items_list import ItemsList
from .components.toasts import ToastNotifications
from .components.vertical_navigation import VerticalNavigation
from .pages.abstract_page import AbstractPage


class MainPageMixin(ToastNotifications, VerticalNavigation, ItemsList, AbstractPage):
    pass
