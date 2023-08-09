from __future__ import annotations

from camayoc.ui.types import UIPage

from .popup import PopUp


class Wizard(UIPage):
    pass


class WizardStep(PopUp, UIPage):
    NEXT_STEP_LOCATOR = '.pf-c-wizard__footer button:has-text("Next")'
    PREV_STEP_LOCATOR = '.pf-c-wizard__footer button:has-text("Back")'
    CANCEL_LOCATOR = ".pf-c-wizard__footer .pf-c-wizard__footer-cancel button"
    NEXT_STEP_RESULT_CLASS = None
    PREV_STEP_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = None

    def next_step(self):
        return self._click_button("NEXT_STEP_LOCATOR", "NEXT_STEP_RESULT_CLASS")

    def prev_step(self):
        return self._click_button("PREV_STEP_LOCATOR", "PREV_STEP_RESULT_CLASS")

    def confirm(self):
        return self.next_step()
