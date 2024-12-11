from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.types.ui import UIPage
from camayoc.ui.enums import Pages

if TYPE_CHECKING:
    from .login import Login


class LoggedIn(UIPage):
    def logout(self) -> Login:
        app_user_dropdown_button = "button[data-ouia-component-id=user_dropdown_button]:visible"
        logout_link = f"{app_user_dropdown_button} ~ div li[data-ouia-component-id=logout]"

        self._driver.click(app_user_dropdown_button)
        self._driver.click(logout_link)

        return self._new_page(Pages.LOGIN)
