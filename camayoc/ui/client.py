from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING
from urllib.parse import urlunparse

from .models.pages.login import Login
from .session import DummySession
from .types import Session
from camayoc import config
from camayoc import exceptions

if TYPE_CHECKING:
    from playwright.sync_api import Page
    from playwright.sync_api import Download
    from camayoc.ui.types import UIPage


class Client:
    def __init__(
        self,
        driver: Page,
        session: Optional[Session] = None,
        url=None,
        auto_dismiss_notification=True,
    ):
        self._camayoc_config = config.get_config()
        self._base_url = url
        self._set_url()
        self._auto_dismiss_notification = auto_dismiss_notification

        self.session = session or DummySession()
        self.downloaded_files: list[Download] = []
        self.driver = driver

    def _set_url(self):
        if self._base_url:
            return

        cfg = self._camayoc_config.get("qpc", {})
        hostname = cfg.get("hostname")

        if not hostname:
            raise exceptions.QPCBaseUrlNotFound(
                "\n'qpc' section specified in camayoc config file, but" "no 'hostname' key found."
            )

        scheme = "https" if cfg.get("https", False) else "http"
        port = str(cfg.get("port", ""))
        netloc = hostname + ":{}".format(port) if port else hostname
        self._base_url = urlunparse((scheme, netloc, "", "", "", ""))

    def begin(self) -> Login:
        """Start browser and open Quipucords UI login page"""
        self.driver.goto(self._base_url)
        return Login(client=self)

    @property
    def current_page(self) -> UIPage:
        """Get instance of object representing currently opened page"""
        pass

    @property
    def history(self) -> None:
        """Get access to Session.history
        FIXME: do I need this?
        """
        pass

    def navigate_to(self) -> UIPage:
        """Wrap self.begin().login(default_user, default_pass).navigate_to("Some Page")
        FIXME: do I need this?
        """
        pass
