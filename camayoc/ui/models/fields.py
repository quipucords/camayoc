from enum import Enum

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError

from camayoc.types.ui import UIField


class Field(UIField):
    def __init__(self, locator: str, transform_input=None):
        self.locator = locator
        self.transform_input_fn = transform_input
        self.parent = None
        self.name = None
        self.driver = None

    def bind(self, parent, name, driver: Page):
        self.parent = parent
        self.name = name
        self.driver = driver

    def pre_fill_transform_input(self, value):
        transform_input_fn = self.transform_input_fn
        if transform_input_fn is None:
            return value
        value = transform_input_fn(value)
        return value

    def fill(self, value):
        value = self.pre_fill_transform_input(value)
        self.do_fill(value)


class CheckboxField(Field):
    def do_fill(self, value):
        elem = self.driver.locator(self.locator)
        current_state = elem.is_checked()
        if value == current_state:
            return

        if value:
            elem.check()
        else:
            elem.uncheck()


class FilteredMultipleSelectField(Field):
    def do_fill(self, value: list[str]):
        filter_input = 'div[data-ouia-component-id="credentials_list_input"] input'

        try:
            self.driver.locator(self.locator).locator(
                "button[data-ouia-component-id=credentials_list_clear_button]"
            ).click(timeout=500)
        except TimeoutError:
            pass

        # First click opens the list. Second hides it and enables us to type.
        self.driver.locator(self.locator).locator(filter_input).click(click_count=2)

        for actual_value in value:
            self.driver.locator(self.locator).locator(filter_input).fill(actual_value)
            values_list = self.driver.locator("body > div[class*=-c-menu] ul[id*=select]")
            label_elem = values_list.locator(f"text='{actual_value}'")
            checkbox_elem = label_elem.locator("xpath=parent::span//input[@type='checkbox']")
            if not checkbox_elem.is_checked():
                label_elem.click()
            self.driver.locator(self.locator).locator(filter_input).clear()

        if values_list.is_visible():
            self.driver.locator(self.locator).locator(filter_input).click()


class InputField(Field):
    def do_fill(self, value):
        input_elem = self.driver.locator(self.locator)
        if input_elem.input_value() == value:
            return
        input_elem.fill(value)


class SecretInputField(InputField):
    def do_fill(self, value):
        input_elem = self.driver.locator(self.locator)
        if input_elem.is_disabled():
            self.driver.click(
                f"div[class*=input-group]:has({self.locator})"
                " button[data-ouia-component-id=secret-edit]"
            )
        super().do_fill(value)


class MultipleSelectField(Field):
    def do_fill(self, value: list[str]):
        self.driver.click(self.locator)
        values_list = self.driver.locator("body > div[class$=-c-menu] ul")
        for actual_value in value:
            values_list.locator(f"text='{actual_value}'").click()

        if values_list.is_visible():
            self.driver.click(self.locator)


class SelectField(Field):
    def do_fill(self, value):
        values_list_locator = "body > div[class*=-c-menu] ul"

        if isinstance(value, Enum) and (enum_value := getattr(value, "value")):
            value = enum_value

        self.driver.click(self.locator)
        values_list = self.driver.locator(values_list_locator)
        values_list.locator(f"text='{value}'").click()
