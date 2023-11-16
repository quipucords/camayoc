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
    from playwright.sync_api import Error
    from playwright.sync_api import Page
    from playwright.sync_api import Request


def requestfailed_handler_factory(ui_client):
    def inner(request: Request):
        error_msg = f"{request.method} {request.url} failed: {request.failure}"
        ui_client._log_page_error(error_msg)

    return inner


def requestfinished_handler_factory(ui_client):
    def inner(request: Request):
        request_response = request.response()
        # if we did not receive a response, then "requestfailed" event should
        # be fired instead of "requestfinished", but Request.response() may
        # return None - so better safe than sorry
        if not request_response:
            error_msg = f"{request.method} {request.url} did not receive a response"
            ui_client._log_page_error(error_msg)
            return

        response_status = request_response.status
        # we are only interested in client and server errors
        if 400 > response_status:
            return
        error_msg = f"{request.method} {request.url} returned {response_status}"
        ui_client._log_page_error(error_msg)

    return inner


def pageerror_handler_factory(ui_client):
    def inner(error: Error):
        error_msg = f"{error.name} {error.message} detected"
        ui_client._log_page_error(error_msg)

    return inner


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
        self.page_errors = []

        self.driver.on("requestfailed", requestfailed_handler_factory(self))
        self.driver.on("requestfinished", requestfinished_handler_factory(self))
        self.driver.on("pageerror", pageerror_handler_factory(self))

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

    def _log_page_error(self, error: str):
        context_msg = f"[issued by {self.driver.url}]"
        error_msg = f"{error} {context_msg}"
        self.page_errors.append(error_msg)

    def begin(self) -> Login:
        """Start browser and open Quipucords UI login page."""
        self.driver.goto(self._base_url)
        return Login(client=self)
