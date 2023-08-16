from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.ui.enums import Pages
from camayoc.ui.types import UIPage

if TYPE_CHECKING:
    from .login import Login


class LoggedIn(UIPage):
    def logout(self) -> Login:
        app_user_dropdown = "div[data-ouia-component-id=user_dropdown]:visible"
        app_user_dropdown_button = f"{app_user_dropdown} > button"
        logout_link = f"{app_user_dropdown} > ul a[data-ouia-component-id=logout]"

        self._driver.click(app_user_dropdown_button)
        self._driver.click(logout_link)

        return self._new_page(Pages.LOGIN)
