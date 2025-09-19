from __future__ import annotations

import time
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

        # Login page has fade in animation set. It has animation delay of 150 ms
        # and animation length of 150 ms. We *think* extremely rare failures that
        # we observe on OpenStack might be caused by Playwright trying to insert
        # letters while animation is ongoing.
        # Unfortunately, Playwright does not seem to provide "animation end" event,
        # so we just explicitly wait for about half a second. If our assumption
        # about failures root cause is correct, this should help.
        time.sleep(0.5)

        if self._driver.locator(login_page_indicator).is_visible():
            self._driver.fill(username_input, data.username)
            self._driver.fill(password_input, data.password)
            self._driver.click(submit_button)

        return self._new_page(Pages.OVERVIEW)
