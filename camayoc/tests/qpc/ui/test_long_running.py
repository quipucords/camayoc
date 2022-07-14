"""Long running (HiVAT) tests.

:caseautomation: automated
:casecomponent: ui
:caseimportance: low
:caselevel: system
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import inspect
import random
from enum import Enum

from playwright.sync_api import TimeoutError

from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui import enums


def is_public_method(callable):
    if not inspect.ismethod(callable):
        return False
    if callable.__name__.startswith("_"):
        return False
    if getattr(callable, "__hvat_hide_method__", False):
        return False
    return True


def get_object_for_type(type_name):
    if (enum_cls := getattr(enums, type_name, None)) and issubclass(enum_cls, Enum):
        return random.choice(list(enum_cls))

    if "DTO" in type_name:
        factory_name = f"{type_name}Factory"
        cls = getattr(data_factories, factory_name, None)
        if not cls:
            raise Exception(f"Can't find {factory_name} in camayoc.ui.data_factories")
        return cls()

    raise Exception(f"I don't know what to do with {type_name}")


def test_long_running(ui_client: Client):
    """Perform random actions on application

    :id: d5941a62-438a-4e95-8041-f55a2ae490c0
    :description: This is proof-of-concept implementation
        of high volume automated testing.
        The robot will perform random operations until it
        encounters exception, which might signify a bug
        in tested system.
    :steps:
        1) Start the robot.
        2) Perform random operations.
    :expectedresults: All operations succeed.
    """
    max_steps = 5
    executed_steps = 0
    page = ui_client.begin()
    while max_steps > executed_steps:
        available_methods = inspect.getmembers(page, is_public_method)
        if not available_methods:
            raise Exception(f"{type(page).__name__} doesn't have any public methods!")

        new_method_name, new_method = random.choice(available_methods)
        print(f"chosen {new_method_name}")
        method_args = {}
        method_params = inspect.signature(new_method, follow_wrapped=True).parameters
        for arg_key, arg_param in method_params.items():
            arg_type_name = arg_param.annotation  # FIXME: what if param doesn't have annotation?
            arg_value = get_object_for_type(arg_type_name)  # FIXME: what if we fail?
            method_args[arg_key] = arg_value

        try:
            page = getattr(page, new_method_name)(**method_args)
            executed_steps += 1
        except (MisconfiguredWidgetException, TimeoutError):
            # We tried saving form without filling it - ignore and try again
            print("Impossible to call {}.{}".format(type(page).__name__, new_method_name))
            pass
