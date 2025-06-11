from __future__ import annotations

from typing import overload

from camayoc.types.ui import AddSourceDTO
from camayoc.types.ui import AnsibleSourceFormDTO
from camayoc.types.ui import NetworkSourceFormDTO
from camayoc.types.ui import NewScanFormDTO
from camayoc.types.ui import OpenShiftSourceFormDTO
from camayoc.types.ui import RHACSSourceFormDTO
from camayoc.types.ui import SatelliteSourceFormDTO
from camayoc.types.ui import TriggerScanDTO
from camayoc.types.ui import VCenterSourceFormDTO
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import Pages
from camayoc.ui.enums import SourceTypes

from ..components.add_new_dropdown import AddNewDropdown
from ..components.form import Form
from ..components.items_list import AbstractListItem
from ..components.popup import PopUp
from ..fields import CheckboxField
from ..fields import FilteredMultipleSelectField
from ..fields import InputField
from ..fields import SelectField
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage


class SourceForm(Form, PopUp, AbstractPage):
    SAVE_RESULT_CLASS = Pages.SOURCES
    CANCEL_RESULT_CLASS = Pages.SOURCES

    @record_action
    def cancel(self) -> SourcesMainPage:
        return super().cancel()

    @creates_toast
    @record_action
    def confirm(self) -> SourcesMainPage:
        return super().confirm()


class NetworkRangeSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        addresses = InputField(
            "textarea[data-ouia-component-id=hosts_multiple]",
            transform_input=lambda i: ",".join(i),
        )
        port = InputField("input[data-ouia-component-id=port]", transform_input=lambda i: str(i))
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        use_paramiko = CheckboxField("input[data-ouia-component-id=options_paramiko]")

    @overload
    def fill(self, data: NetworkSourceFormDTO): ...

    @record_action
    def fill(self, data: NetworkSourceFormDTO):
        super().fill(data)
        return self


class SatelliteSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        port = InputField("input[data-ouia-component-id=port]")
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        connection = SelectField("button[data-ouia-component-id=options_ssl_protocol]")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: SatelliteSourceFormDTO): ...

    @record_action
    def fill(self, data: SatelliteSourceFormDTO):
        super().fill(data)
        return self


class VCenterSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        port = InputField("input[data-ouia-component-id=port]")
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        connection = SelectField("button[data-ouia-component-id=options_ssl_protocol]")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: VCenterSourceFormDTO): ...

    @record_action
    def fill(self, data: VCenterSourceFormDTO):
        super().fill(data)
        return self


class OpenShiftSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        port = InputField("input[data-ouia-component-id=port]")
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        connection = SelectField("button[data-ouia-component-id=options_ssl_protocol]")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: OpenShiftSourceFormDTO): ...

    @record_action
    def fill(self, data: OpenShiftSourceFormDTO):
        super().fill(data)
        return self


class AnsibleSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        port = InputField("input[data-ouia-component-id=port]")
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        connection = SelectField("button[data-ouia-component-id=options_ssl_protocol]")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: AnsibleSourceFormDTO): ...

    @record_action
    def fill(self, data: AnsibleSourceFormDTO):
        super().fill(data)
        return self


class RHACSSourceCredentialsForm(SourceForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        port = InputField("input[data-ouia-component-id=port]")
        credentials = FilteredMultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select]"
        )
        connection = SelectField("button[data-ouia-component-id=options_ssl_protocol]")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: RHACSSourceFormDTO): ...

    @record_action
    def fill(self, data: RHACSSourceFormDTO):
        super().fill(data)
        return self


class ScanForm(Form, PopUp, AbstractPage):
    SAVE_RESULT_CLASS = Pages.SOURCES
    CANCEL_RESULT_CLASS = Pages.SOURCES

    class FormDefinition:
        scan_name = InputField("input[data-ouia-component-id=name][id=scan-name]")
        max_concurrent_scans = InputField("div[data-ouia-component-id=scan_concurrency] input")
        jboss_eap = CheckboxField("input[data-ouia-component-id=options_jboss_eap]")
        fuse = CheckboxField("input[data-ouia-component-id=options_jboss_fuse]")
        jboss_web_server = CheckboxField("input[data-ouia-component-id=options_jboss_ws]")
        alternate_dirs = InputField("textarea[data-ouia-component-id=scan_alt_dirs]")

    @overload
    def fill(self, data: NewScanFormDTO): ...

    @record_action
    def fill(self, data: NewScanFormDTO):
        super().fill(data)
        return self


class SourceListElem(AbstractListItem):
    def open_scan(self) -> ScanForm:
        scan_locator = 'button[data-ouia-component-id="scan_button"]'
        self.locator.locator(scan_locator).click()
        return ScanForm(client=self._client)


SOURCE_TYPE_MAP = {
    SourceTypes.NETWORK_RANGE: {
        "ouiaid": "network",
        "class": NetworkRangeSourceCredentialsForm,
    },
    SourceTypes.SATELLITE: {
        "ouiaid": "satellite",
        "class": SatelliteSourceCredentialsForm,
    },
    SourceTypes.VCENTER_SERVER: {
        "ouiaid": "vcenter",
        "class": VCenterSourceCredentialsForm,
    },
    SourceTypes.OPENSHIFT: {
        "ouiaid": "openshift",
        "class": OpenShiftSourceCredentialsForm,
    },
    SourceTypes.ANSIBLE_CONTROLLER: {
        "ouiaid": "ansible",
        "class": AnsibleSourceCredentialsForm,
    },
    SourceTypes.RHACS: {
        "ouiaid": "rhacs",
        "class": RHACSSourceCredentialsForm,
    },
}


class SourcesMainPage(AddNewDropdown, MainPageMixin):
    ITEM_CLASS = SourceListElem
    ADD_BUTTON_LOCATOR = "button[data-ouia-component-id=add_source_button]"

    @service
    def add_source(self, data: AddSourceDTO) -> SourcesMainPage:
        add_sources_popup = self.open_add_source(data.source_type)
        add_sources_popup.fill(data.source_form)
        return add_sources_popup.confirm()

    @service
    def edit_source(self, name: str, data: AddSourceDTO) -> SourcesMainPage:
        edit_source_popup = self.open_edit_source(name, data.source_type)
        edit_source_popup.fill(data.source_form)
        return edit_source_popup.confirm()

    @record_action
    def open_add_source(self, source_type: SourceTypes) -> SourceForm:
        ouiaid, cls = SOURCE_TYPE_MAP.get(source_type).values()
        self.open_create_new_modal(type_ouiaid=ouiaid)
        return self._new_page(cls)

    @record_action
    def open_edit_source(self, name: str, source_type: SourceTypes) -> SourceForm:
        cls = SOURCE_TYPE_MAP.get(source_type).get("class")
        item: SourceListElem = self._get_item(name)
        item.select_action("edit-source")
        return self._new_page(cls)

    @creates_toast
    @record_action
    def trigger_scan(self, data: TriggerScanDTO) -> SourcesMainPage:
        item: SourceListElem = self._get_item(data.source_name)
        popup = item.open_scan()
        popup.fill(data.scan_form)
        return popup.confirm()
