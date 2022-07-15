from .components.items_list import ItemsList
from .components.logged_in import LoggedIn
from .components.toasts import ToastNotifications
from .components.vertical_navigation import VerticalNavigation
from .pages.abstract_page import AbstractPage


class MainPageMixin(ToastNotifications, LoggedIn, VerticalNavigation, ItemsList, AbstractPage):
    pass
