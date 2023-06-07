from __future__ import annotations

from typing import TYPE_CHECKING

from camayoc.ui.decorators import record_action
from camayoc.ui.enums import Pages
from camayoc.ui.types import LoginFormDTO

from .abstract_page import AbstractPage

if TYPE_CHECKING:
    from .sources import SourcesMainPage


class Login(AbstractPage):
    @record_action
    def login(self, data: LoginFormDTO) -> SourcesMainPage:
        login_page_indicator = "html.login-pf"
        username_input = "input[name=username]"
        password_input = "input[name=password]"
        submit_button = "button[type=submit]"

        if self._driver.locator(login_page_indicator).is_visible():
            self._driver.fill(username_input, data.username)
            self._driver.fill(password_input, data.password)
            self._driver.click(submit_button)

        return self._new_page(Pages.SOURCES)
