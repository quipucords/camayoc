from __future__ import annotations

from .popup import PopUp
from camayoc.ui.types import UIPage


class Wizard(UIPage):
    pass


class WizardStep(PopUp, UIPage):
    NEXT_STEP_LOCATOR = '.modal-footer button:has-text("Next")'
    PREV_STEP_LOCATOR = '.modal-footer button:has-text("Back")'
    CANCEL_LOCATOR = ".modal-footer button.btn-cancel"
    NEXT_STEP_RESULT_CLASS = None
    PREV_STEP_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = None

    def next_step(self):
        return self._click_button("NEXT_STEP_LOCATOR", "NEXT_STEP_RESULT_CLASS")

    def prev_step(self):
        return self._click_button("PREV_STEP_LOCATOR", "PREV_STEP_RESULT_CLASS")

    def confirm(self):
        return self.next_step()
