from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.types.ui import LoginFormDTO
from camayoc.ui.decorators import record_action
from camayoc.ui.enums import Pages

from .abstract_page import AbstractPage

if TYPE_CHECKING:
    from .credentials import CredentialsMainPage


class Login(AbstractPage):
    @record_action
    def login(self, data: LoginFormDTO) -> CredentialsMainPage:
        login_page_indicator = "main[class$=login__main]"
        username_input = "input[name=pf-login-username-id]"
        password_input = "input[name=pf-login-password-id]"
        submit_button = "button[type=submit]"

        if self._driver.locator(login_page_indicator).is_visible():
            self._driver.fill(username_input, data.username)
            self._driver.fill(password_input, data.password)
            self._driver.click(submit_button)

        return self._new_page(Pages.CREDENTIALS)
