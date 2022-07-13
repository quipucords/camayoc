from __future__ import annotations

import logging

from attrs import fields

from ..fields import Field
from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.ui.types import UIField
from camayoc.ui.types import UIPage

logger = logging.getLogger(__name__)


class Form(UIPage):
    def fill(self, data):
        form_definition = getattr(self, "FormDefinition")
        if not form_definition:
            msg = "{} requires class property 'FormDefinition' to be set [object={}]"
            raise MisconfiguredWidgetException(msg.format(type(self).__name__, self))

        field_names = [f.name for f in fields(type(data))]
        form_fields = [f for f in form_definition.__dict__ if not f.startswith("_")]
        ordered_field_names = [f for f in form_fields if f in field_names]

        for field_name in ordered_field_names:
            field: UIField = getattr(form_definition, field_name)
            if not isinstance(field, Field):
                logger.debug(
                    "%s.FormDefinition.%s is not instance of Field, skipping",
                    type(self).__name__,
                    field_name,
                )
                continue

            field.bind(parent=self, name=field_name, driver=self._driver)
            value = getattr(data, field_name, None)
            if value is None:
                logger.debug(
                    "%s field %s is None, skipping",
                    type(data).__name__,
                    field_name,
                )
                continue

            logger.debug("Filling field '%s' with value '%s'", field_name, value)
            field.fill(value)
