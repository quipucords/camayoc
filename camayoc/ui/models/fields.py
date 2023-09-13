from enum import Enum

from playwright.sync_api import Page

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


class InputField(Field):
    def do_fill(self, value):
        self.driver.fill(self.locator, value)


class MultipleSelectField(Field):
    def do_fill(self, value: list[str]):
        self.driver.click(self.locator)
        values_list = self.driver.locator(self.locator).locator("xpath=following-sibling::ul")
        for actual_value in value:
            values_list.locator(f"text='{actual_value}'").click()

        if values_list.is_visible():
            self.driver.click(self.locator)


class RadioGroupField(Field):
    def do_fill(self, value):
        if isinstance(value, Enum) and (enum_value := getattr(value, "value")):
            value = enum_value

        radio_group = self.driver.locator(self.locator)
        radio_group.locator(f"input[value={value}]").check()


class SelectField(Field):
    def do_fill(self, value):
        if isinstance(value, Enum) and (enum_value := getattr(value, "value")):
            value = enum_value

        self.driver.click(self.locator)
        values_list = self.driver.locator(self.locator).locator("xpath=following-sibling::ul")
        values_list.locator(f"text='{value}'").click()
