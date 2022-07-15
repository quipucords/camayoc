from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.ui.enums import Pages
from camayoc.ui.types import UIPage

if TYPE_CHECKING:
    from .login import Login


class LoggedIn(UIPage):
    def logout(self) -> Login:
        app_user_dropdown = "button#app-user-dropdown"
        logout_link = f"{app_user_dropdown} ~ ul a[displaytitle=Logout]"

        self._driver.click(app_user_dropdown)
        self._driver.click(logout_link)

        return self._new_page(Pages.LOGIN)
