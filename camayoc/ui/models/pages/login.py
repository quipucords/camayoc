from __future__ import annotations

from typing import TYPE_CHECKING

from .abstract_page import AbstractPage
from camayoc.ui.enums import Pages
from camayoc.ui.types import LoginFormDTO

if TYPE_CHECKING:
    from .sources import SourcesMainPage


class Login(AbstractPage):
    def login(self, data: LoginFormDTO) -> SourcesMainPage:
        login_page_indicator = "html.login-pf"
        username_input = "input[name=username]"
        password_input = "input[name=password]"
        submit_button = "button[type=submit]"

        # FIXME: switch to factory
        if data.username is None and data.password is None:
            data = LoginFormDTO(
                username=self._client._camayoc_config.get("qpc", {}).get("username"),
                password=self._client._camayoc_config.get("qpc", {}).get("password"),
            )

        if self._driver.locator(login_page_indicator).is_visible():
            self._driver.fill(username_input, data.username)
            self._driver.fill(password_input, data.password)
            self._driver.click(submit_button)

        return self._new_page(Pages.SOURCES)
