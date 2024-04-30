from __future__ import annotations

from typing import overload

from camayoc.types.ui import AddCredentialDTO
from camayoc.types.ui import AnsibleCredentialFormDTO
from camayoc.types.ui import NetworkCredentialFormDTO
from camayoc.types.ui import OpenShiftCredentialFormDTO
from camayoc.types.ui import RHACSCredentialFormDTO
from camayoc.types.ui import SatelliteCredentialFormDTO
from camayoc.types.ui import VCenterCredentialFormDTO
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import Pages

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
        authentication_type = SelectField("div[data-ouia-component-id=auth_type] > button")
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        username = InputField("input[data-ouia-component-id=username]")
        password = InputField("input[data-ouia-component-id=password]")
        ssh_key_file = InputField("input[data-ouia-component-id=ssh_keyfile]")
        passphrase = InputField("input[data-ouia-component-id=ssh_passphrase]")
        become_method = SelectField("div[data-ouia-component-id=become_method] > button")
        become_user = InputField("input[data-ouia-component-id=become_user]")
        become_password = InputField("input[data-ouia-component-id=become_password]")

    @overload
    def fill(self, data: NetworkCredentialFormDTO): ...

    @record_action
    def fill(self, data: NetworkCredentialFormDTO):
        super().fill(data)
        return self


class SatelliteCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        username = InputField("input[data-ouia-component-id=username]")
        password = InputField("input[data-ouia-component-id=password]")

    @overload
    def fill(self, data: SatelliteCredentialFormDTO): ...

    @record_action
    def fill(self, data: SatelliteCredentialFormDTO):
        super().fill(data)
        return self


class VCenterCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        username = InputField("input[data-ouia-component-id=username]")
        password = InputField("input[data-ouia-component-id=password]")

    @overload
    def fill(self, data: VCenterCredentialFormDTO): ...

    @record_action
    def fill(self, data: VCenterCredentialFormDTO):
        super().fill(data)
        return self


class OpenShiftCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        token = InputField("input[data-ouia-component-id=auth_token]")

    @overload
    def fill(self, data: OpenShiftCredentialFormDTO): ...

    @record_action
    def fill(self, data: OpenShiftCredentialFormDTO):
        super().fill(data)
        return self


class AnsibleCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        username = InputField("input[data-ouia-component-id=username]")
        password = InputField("input[data-ouia-component-id=password]")

    @overload
    def fill(self, data: AnsibleCredentialFormDTO): ...

    @record_action
    def fill(self, data: AnsibleCredentialFormDTO):
        super().fill(data)
        return self


class RHACSCredentialForm(CredentialForm):
    class FormDefinition:
        credential_name = InputField("input[data-ouia-component-id=cred_name]")
        token = InputField("input[data-ouia-component-id=auth_token]")

    @overload
    def fill(self, data: RHACSCredentialFormDTO): ...

    @record_action
    def fill(self, data: RHACSCredentialFormDTO):
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
        create_credential_button = "div[data-ouia-component-id=add_credential] > button"
        source_type_map = {
            CredentialTypes.NETWORK: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=network]",
                "class": NetworkCredentialForm,
            },
            CredentialTypes.SATELLITE: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=satellite]",
                "class": SatelliteCredentialForm,
            },
            CredentialTypes.VCENTER: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=vcenter]",
                "class": VCenterCredentialForm,
            },
            CredentialTypes.OPENSHIFT: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=openshift]",
                "class": OpenShiftCredentialForm,
            },
            CredentialTypes.ANSIBLE: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=ansible]",
                "class": AnsibleCredentialForm,
            },
            CredentialTypes.RHACS: {
                "selector": f"{create_credential_button} ~ ul li a[data-value=rhacs]",
                "class": RHACSCredentialForm,
            },
        }

        selector, cls = source_type_map.get(source_type).values()

        self._driver.click(create_credential_button)
        self._driver.click(selector)

        return self._new_page(cls)
