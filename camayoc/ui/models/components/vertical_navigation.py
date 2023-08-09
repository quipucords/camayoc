from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal
from typing import Union
from typing import overload

from camayoc.ui.decorators import record_action
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import Pages
from camayoc.ui.types import UIPage

if TYPE_CHECKING:
    from ..credentials import CredentialsMainPage
    from ..scans import ScansMainPage
    from ..sources import SourcesMainPage

    NavigateToPage = Union[CredentialsMainPage, ScansMainPage, SourcesMainPage]

LEFT_NAV = "nav.pf-c-nav"


class VerticalNavigation(UIPage):
    @overload
    def navigate_to(self, page_name: Literal[MainMenuPages.CREDENTIALS]) -> CredentialsMainPage:
        ...

    @overload
    def navigate_to(self, page_name: Literal[MainMenuPages.SOURCES]) -> SourcesMainPage:
        ...

    @overload
    def navigate_to(self, page_name: Literal[MainMenuPages.SCANS]) -> ScansMainPage:
        ...

    @overload
    def navigate_to(self, page_name: MainMenuPages) -> NavigateToPage:
        ...

    @record_action
    def navigate_to(self, page_name: MainMenuPages) -> NavigateToPage:
        selector = f"text={page_name.value}"
        menu = self._driver.locator(LEFT_NAV)
        menu.locator(selector).click()

        new_page_cls = getattr(Pages, page_name.name)
        return self._new_page(new_page_cls)
