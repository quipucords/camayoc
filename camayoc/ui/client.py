from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional
from urllib.parse import urlunparse

from camayoc import exceptions
from camayoc.config import settings
from camayoc.types.settings import Configuration
from camayoc.types.ui import Session

from .models.pages.login import Login
from .session import DummySession

if TYPE_CHECKING:
    from playwright.sync_api import Download
    from playwright.sync_api import Page


class Client:
    def __init__(
        self,
        driver: Page,
        session: Optional[Session] = None,
        url=None,
        auto_dismiss_notification=True,
    ):
        self._camayoc_config: Configuration = settings
        self._base_url = url
        self._set_url()
        self._auto_dismiss_notification = auto_dismiss_notification

        self.session = session or DummySession()
        self.downloaded_files: list[Download] = []
        self.driver = driver

    def _set_url(self):
        if self._base_url:
            return

        hostname = self._camayoc_config.quipucords_server.hostname

        if not hostname:
            msg = (
                "\n'quipucords_server' section specified in camayoc config file, "
                "but no 'hostname' key found."
            )
            raise exceptions.QPCBaseUrlNotFound(msg)

        scheme = "https" if self._camayoc_config.quipucords_server.https else "http"
        port = str(self._camayoc_config.quipucords_server.port)
        netloc = hostname + ":{}".format(port) if port else hostname
        self._base_url = urlunparse((scheme, netloc, "", "", "", ""))

    def begin(self) -> Login:
        """Start browser and open Quipucords UI login page."""
        self.driver.goto(self._base_url)
        return Login(client=self)
