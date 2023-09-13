from __future__ import annotations

from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.types.ui import UIPage


class PopUp(UIPage):
    SAVE_LOCATOR = ".pf-c-modal-box__footer button.pf-m-primary"
    CANCEL_LOCATOR = ".pf-c-modal-box__footer button.pf-m-secondary"
    SAVE_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = None

    def _get_result_class_name(self, class_name_id) -> str:
        class_name = getattr(self, class_name_id)
        if class_name is None:
            msg = "{} requires class property '{}' to be set [object={}]"
            raise MisconfiguredWidgetException(msg.format(type(self).__name__, class_name_id, self))
        return class_name

    def _click_button(self, selector_property_name, result_property_name):
        selector = getattr(self, selector_property_name)
        self._driver.click(selector)
        result_class = self._get_result_class_name(result_property_name)
        return self._new_page(result_class)

    def confirm(self):
        return self._click_button("SAVE_LOCATOR", "SAVE_RESULT_CLASS")

    def cancel(self):
        return self._click_button("CANCEL_LOCATOR", "CANCEL_RESULT_CLASS")
