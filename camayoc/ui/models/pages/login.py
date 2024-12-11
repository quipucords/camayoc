from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.types.ui import LoginFormDTO
from camayoc.ui.decorators import record_action
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import Pages

from .abstract_page import AbstractPage

if TYPE_CHECKING:
    from .sources import SourcesMainPage


class Login(AbstractPage):
    @record_action
    def login(self, data: LoginFormDTO) -> SourcesMainPage:
        login_page_indicator = "main[class$=login__main]"
        username_input = "input[name=pf-login-username-id]"
        password_input = "input[name=pf-login-password-id]"
        submit_button = "button[type=submit]"

        if self._driver.locator(login_page_indicator).is_visible():
            self._driver.fill(username_input, data.username)
            self._driver.fill(password_input, data.password)
            self._driver.click(submit_button)

        # The new UI opens Credentials page right after login,
        # but we need to navigate to Sources to keep interface
        # compatibility. In most cases it means that we log in,
        # click Sources in menu and immediately go back to Credentials.
        # Oh well...
        credentials_page = self._new_page(Pages.CREDENTIALS)
        return credentials_page.navigate_to(MainMenuPages.SOURCES)
