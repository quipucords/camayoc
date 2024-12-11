from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING
from typing import Union

from camayoc.exceptions import PageFactoryException
from camayoc.types.ui import UIPage
from camayoc.ui.enums import Pages

if TYPE_CHECKING:
    import camayoc

    ClassOrPage = Union[Pages, "AbstractPage"]


class AbstractPage(UIPage):
    def __init__(self, client: camayoc.ui.client.Client):
        self._client = client
        self._driver = client.driver

    def _new_page(self, class_or_page: ClassOrPage) -> UIPage:
        cls = None

        if isinstance(class_or_page, type) and issubclass(class_or_page, AbstractPage):
            cls = class_or_page
        elif isinstance(class_or_page, Pages):
            module_path, class_name = class_or_page.value.split(".", 1)
            module = import_module(f"camayoc.ui.models.pages.{module_path}")
            cls = getattr(module, class_name)

        if not cls:
            msg = (
                "Can't create new page from '{}' (type: '{}')\n"
                "Expected class (not instance) inheriting from AbstractPage, "
                "or value from Pages enum."
            )
            raise PageFactoryException(msg.format(class_or_page, type(class_or_page).__name__))

        return cls(client=self._client)
