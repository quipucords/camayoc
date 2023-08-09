from __future__ import annotations

from typing import overload

from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import Pages
from camayoc.ui.types import AddCredentialDTO
from camayoc.ui.types import NetworkCredentialFormDTO
from camayoc.ui.types import SatelliteCredentialFormDTO
from camayoc.ui.types import VCenterCredentialFormDTO

from ..components.form import Form
from ..components.popup import PopUp
from ..fields import InputField
from ..fields import SelectField
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage


class CredentialForm(Form, PopUp, AbstractPage):
    SAVE_RESULT_CLASS = Pages.CREDENTIALS
    CANCEL_RESULT_CLASS = Pages.CREDENTIALS

    @record_action
    def cancel(self) -> CredentialsMainPage:
        return super().cancel()

    @creates_toast
    @record_action
    def confirm(self) -> CredentialsMainPage:
        return super().confirm()


class NetworkCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[placeholder$=credential]")
        authentication_type = SelectField("button#auth-type-select")
        username = InputField("input[placeholder$=username]")
        password = InputField("input[placeholder$=password]")
        ssh_key_file = InputField('label:has-text("SSH Key File") + div input')
        passphrase = InputField('label:has-text("Passphrase") + div input')
        become_method = SelectField("button#become-method-select")
        become_user = InputField('label:has-text("Become User") + div input')
        become_password = InputField('label:has-text("Become Password") + div input')

    @overload
    def fill(self, data: NetworkCredentialFormDTO):
        ...

    @record_action
    def fill(self, data: NetworkCredentialFormDTO):
        super().fill(data)
        return self


class SatelliteCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[placeholder$=credential]")
        username = InputField("input[placeholder$=username]")
        password = InputField("input[placeholder$=password]")

    @overload
    def fill(self, data: SatelliteCredentialFormDTO):
        ...

    @record_action
    def fill(self, data: SatelliteCredentialFormDTO):
        super().fill(data)
        return self


class VCenterCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[placeholder$=credential]")
        username = InputField("input[placeholder$=username]")
        password = InputField("input[placeholder$=password]")

    @overload
    def fill(self, data: VCenterCredentialFormDTO):
        ...

    @record_action
    def fill(self, data: VCenterCredentialFormDTO):
        super().fill(data)
        return self


class CredentialsMainPage(MainPageMixin):
    @service
    def add_credential(self, data: AddCredentialDTO) -> CredentialsMainPage:
        add_credential_popup = self.open_add_credential(data.credential_type)
        add_credential_popup.fill(data.credential_form_dto)
        return add_credential_popup.confirm()

    @record_action
    def open_add_credential(self, source_type: CredentialTypes) -> CredentialForm:
        create_credential_button = "#createCredentialButton"
        source_type_map = {
            CredentialTypes.NETWORK: {
                "selector": f"{create_credential_button} ~ ul li:nth-of-type(1) a",
                "class": NetworkCredentialForm,
            },
            CredentialTypes.SATELLITE: {
                "selector": f"{create_credential_button} ~ ul li:nth-of-type(3) a",
                "class": SatelliteCredentialForm,
            },
            CredentialTypes.VCENTER: {
                "selector": f"{create_credential_button} ~ ul li:nth-of-type(4) a",
                "class": VCenterCredentialForm,
            },
        }

        selector, cls = source_type_map.get(source_type).values()

        self._driver.click(create_credential_button)
        self._driver.click(selector)

        return self._new_page(cls)
