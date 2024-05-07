from __future__ import annotations

from typing import Optional

from playwright.sync_api import Locator
from playwright.sync_api import TimeoutError

from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.types.ui import UIListItem
from camayoc.types.ui import UIPage


class AbstractListItem(UIListItem):
    def __init__(self, locator: Locator, client):
        self.locator = locator
        self._client = client


class ItemsList(UIPage):
    ITEM_CLASS: Optional[AbstractListItem] = None

    def _get_item_from_current_list(self, name: str):
        default_timeout = 5000  # 5s
        item_elem = self._driver.locator("css=strong").filter(has_text=name)
        item_elem_locator = "xpath=./ancestor::tr[contains(@class, 'quipucords-table__tr')]"
        item_elem = item_elem.locator(item_elem_locator)
        item_elem.hover(timeout=default_timeout, trial=True)
        return item_elem

    # We probably should have separate component for filters
    # that exposes wider array of actions (filtering by any field,
    # by multiple fileds, clearing filters, sorting?).
    # But YAGNI tells us this will do for now
    def _search_for_item_by_name(self, name: str):
        filter_field_button = self._driver.locator(
            "div[class*=-c-toolbar__content] button[id]:has(span[class*=-c-select__toggle-arrow])"
        ).locator("nth=0")
        if filter_field_button.text_content() != "Name":
            filter_field_button.click()
            values_list = filter_field_button.locator("xpath=following-sibling::ul")
            values_list.locator("text='Name'").click()
        self._driver.fill("input[placeholder$=name]", name)
        self._driver.keyboard.press("Enter")

    def _get_item(self, name: str):
        item_cls: AbstractListItem = getattr(self, "ITEM_CLASS")
        if not item_cls:
            msg = "{} requires class property 'ITEM_CLASS' to be set [object={}]"
            raise MisconfiguredWidgetException(msg.format(type(self).__name__, self))

        try:
            item_elem = self._get_item_from_current_list(name)
        except TimeoutError:
            self._search_for_item_by_name(name)
            item_elem = self._get_item_from_current_list(name)

        return item_cls(item_elem, client=self._client)
