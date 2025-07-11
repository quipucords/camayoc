from __future__ import annotations

from typing import Optional

from playwright.sync_api import Locator
from playwright.sync_api import TimeoutError

from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.types.ui import UIListItem
from camayoc.types.ui import UIPage


class AbstractListItem(UIListItem):
    ACTION_MENU_TOGGLE_LOCATOR = "button[data-ouia-component-id=action_menu_toggle]"
    ACTION_MENU_ITEM_LOCATOR_TEMPLATE = (
        ACTION_MENU_TOGGLE_LOCATOR + "~ div *[data-ouia-component-id={ouiaid}] button"
    )

    def __init__(self, locator: Locator, client):
        self.locator = locator
        self._client = client

    def select_action(self, ouiaid: str, timeout: int = 30_000) -> None:
        self._open_kebab()
        item_locator = self.ACTION_MENU_ITEM_LOCATOR_TEMPLATE.format(ouiaid=ouiaid)
        self.locator.locator(item_locator).click(timeout=timeout)

    def _open_kebab(self) -> None:
        toggle_elem = self.locator.locator(self.ACTION_MENU_TOGGLE_LOCATOR)
        if str(toggle_elem.get_attribute("aria-expanded")).lower() == "true":
            return
        toggle_elem.click()


class ItemsList(UIPage):
    ITEM_CLASS: Optional[AbstractListItem] = None

    def _get_item_from_current_list(self, name: str):
        default_timeout = 5000  # 5s
        item_label_locator = "td[data-label=Name]"
        item_elem_locator = "xpath=./ancestor::tr[contains(@class, 'table__tr')]"

        item_elem = self._driver.locator(item_label_locator).filter(
            has=self._driver.get_by_text(name, exact=True)
        )
        item_elem = item_elem.locator(item_elem_locator)
        item_elem.hover(timeout=default_timeout, trial=True)
        return item_elem

    # We probably should have separate component for filters
    # that exposes wider array of actions (filtering by any field,
    # by multiple fields, clearing filters, sorting?).
    # But YAGNI tells us this will do for now
    def _search_for_item_by_name(self, name: str):
        filter_field_button_locator = (
            "div[class*=-c-toolbar__item] button[id]:has(span[class*=-c-menu-toggle])"
        )
        filter_field_values_locator = "xpath=following-sibling::div[contains(@class, '-c-menu')]"

        filter_field_button = self._driver.locator(filter_field_button_locator).locator("nth=0")
        if filter_field_button.text_content() != "Name":
            filter_field_button.click()
            values_list = filter_field_button.locator(filter_field_values_locator)
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
