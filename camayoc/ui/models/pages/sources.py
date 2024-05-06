from __future__ import annotations

from typing import overload

from camayoc.types.ui import AddSourceDTO
from camayoc.types.ui import AnsibleSourceFormDTO
from camayoc.types.ui import NetworkSourceFormDTO
from camayoc.types.ui import NewScanFormDTO
from camayoc.types.ui import OpenShiftSourceFormDTO
from camayoc.types.ui import RHACSSourceFormDTO
from camayoc.types.ui import SatelliteSourceFormDTO
from camayoc.types.ui import SelectSourceDTO
from camayoc.types.ui import TriggerScanDTO
from camayoc.types.ui import VCenterSourceFormDTO
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import Pages
from camayoc.ui.enums import SourceTypes

from ..components.form import Form
from ..components.items_list import AbstractListItem
from ..components.popup import PopUp
from ..components.wizard import WizardStep
from ..fields import CheckboxField
from ..fields import InputField
from ..fields import MultipleSelectField
from ..fields import RadioGroupField
from ..fields import SelectField
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage


class CancelWizardPopup(PopUp, AbstractPage):
    SAVE_LOCATOR = ".pf-c-modal-box__footer button.pf-m-primary:text-is('Yes')"
    CANCEL_LOCATOR = ".pf-c-modal-box__footer button.pf-m-secondary:text-is('No')"
    SAVE_RESULT_CLASS = Pages.SOURCES
    CANCEL_RESULT_CLASS = None


class SelectSourceTypeForm(Form, WizardStep, AbstractPage):
    NEXT_STEP_RESULT_CLASS = None
    PREV_STEP_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = CancelWizardPopup

    class FormDefinition:
        source_type = RadioGroupField("div.pf-c-wizard__main-body:not(.hidden)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self, "NEXT_STEP_RESULT_CLASS", NetworkRangeSourceCredentialsForm)

    def cancel(self) -> CancelWizardPopup:
        popup = super().cancel()
        setattr(popup, "CANCEL_RESULT_CLASS", type(self))
        return popup

    def fill(self, data: SelectSourceDTO):
        source_type_map = {
            SourceTypes.NETWORK_RANGE: NetworkRangeSourceCredentialsForm,
            SourceTypes.SATELLITE: SatelliteSourceCredentialsForm,
            SourceTypes.VCENTER_SERVER: VCenterSourceCredentialsForm,
            SourceTypes.OPENSHIFT: OpenShiftSourceCredentialsForm,
            SourceTypes.ANSIBLE_CONTROLLER: AnsibleSourceCredentialsForm,
            SourceTypes.RHACS: RHACSSourceCredentialsForm,
        }
        next_step_class = source_type_map.get(data.source_type)
        setattr(self, "NEXT_STEP_RESULT_CLASS", next_step_class)
        super().fill(data)
        return self


class SourceCredentialsForm(Form, WizardStep, AbstractPage):
    NEXT_STEP_LOCATOR = '.pf-c-wizard__footer button:has-text("Save")'
    NEXT_STEP_RESULT_CLASS = Pages.SOURCES_RESULTS_PAGE
    PREV_STEP_RESULT_CLASS = SelectSourceTypeForm
    CANCEL_RESULT_CLASS = CancelWizardPopup

    def cancel(self) -> CancelWizardPopup:
        popup = super().cancel()
        setattr(popup, "CANCEL_RESULT_CLASS", type(self))
        return popup


class NetworkRangeSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        addresses = InputField(
            "textarea[data-ouia-component-id=hosts_multiple]",
            transform_input=lambda i: ",".join(i),
        )
        port = InputField("input[data-ouia-component-id=port]", transform_input=lambda i: str(i))
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        use_paramiko = CheckboxField("input[data-ouia-component-id=options_paramiko]")

    @overload
    def fill(self, data: NetworkSourceFormDTO):
        ...

    @record_action
    def fill(self, data: NetworkSourceFormDTO):
        super().fill(data)
        return self


class SatelliteSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        connection = SelectField("div[data-ouia-component-id=options_ssl_protocol] > button")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: SatelliteSourceFormDTO):
        ...

    @record_action
    def fill(self, data: SatelliteSourceFormDTO):
        super().fill(data)
        return self


class VCenterSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        connection = SelectField("div[data-ouia-component-id=options_ssl_protocol] > button")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: VCenterSourceFormDTO):
        ...

    @record_action
    def fill(self, data: VCenterSourceFormDTO):
        super().fill(data)
        return self


class OpenShiftSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        connection = SelectField("div[data-ouia-component-id=options_ssl_protocol] > button")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: OpenShiftSourceFormDTO):
        ...

    @record_action
    def fill(self, data: OpenShiftSourceFormDTO):
        super().fill(data)
        return self


class AnsibleSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        connection = SelectField("div[data-ouia-component-id=options_ssl_protocol] > button")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: AnsibleSourceFormDTO):
        ...

    @record_action
    def fill(self, data: AnsibleSourceFormDTO):
        super().fill(data)
        return self


class RHACSSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField("input[data-ouia-component-id=name]")
        address = InputField("input[data-ouia-component-id=hosts_single]")
        credentials = MultipleSelectField(
            "div[data-ouia-component-id=add_credentials_select] > button"
        )
        connection = SelectField("div[data-ouia-component-id=options_ssl_protocol] > button")
        verify_ssl = CheckboxField("input[data-ouia-component-id=options_ssl_cert]")

    @overload
    def fill(self, data: RHACSSourceFormDTO):
        ...

    @record_action
    def fill(self, data: RHACSSourceFormDTO):
        super().fill(data)
        return self


class ResultForm(WizardStep, AbstractPage):
    NEXT_STEP_LOCATOR = ".pf-c-wizard__footer button.pf-m-primary"
    NEXT_STEP_RESULT_CLASS = Pages.SOURCES

    def confirm(self):
        locator_template = ".pf-c-wizard svg[data-test-state={state}]"
        fulfilled_elem = self._driver.locator(locator_template.format(state="fulfilled"))
        error_elem = self._driver.locator(locator_template.format(state="error"))
        fulfilled_elem.or_(error_elem).hover(trial=True)
        return super().confirm()


class ScanForm(Form, PopUp, AbstractPage):
    SAVE_RESULT_CLASS = Pages.SOURCES
    CANCEL_RESULT_CLASS = Pages.SOURCES

    class FormDefinition:
        scan_name = InputField("input[name=scanName]")
        max_concurrent_scans = InputField("input#scanConcurrency")
        jboss_eap = CheckboxField("input[name=jbossEap]")
        fuse = CheckboxField("input[name=jbossFuse]")
        jboss_web_server = CheckboxField("input[name=jbossWs]")
        alternate_dirs = InputField("textarea[name=displayScanDirectories]")

    @overload
    def fill(self, data: NewScanFormDTO):
        ...

    @record_action
    def fill(self, data: NewScanFormDTO):
        super().fill(data)
        return self


class SourceListElem(AbstractListItem):
    def open_scan(self) -> ScanForm:
        scan_locator = 'td.quipucords-table__td-action button:has-text("Scan")'
        self.locator.locator(scan_locator).click()
        return ScanForm(client=self._client)


class SourcesMainPage(MainPageMixin):
    ITEM_CLASS = SourceListElem

    @service
    def add_source(self, data: AddSourceDTO) -> SourcesMainPage:
        add_source_wizard = self.open_add_source()
        # page 1 - Select source type
        add_source_wizard.fill(data.select_source_type)
        add_source_wizard = add_source_wizard.next_step()
        # page 2 - main form
        add_source_wizard.fill(data.source_form)
        add_source_wizard = add_source_wizard.next_step()
        # page 3 - summary / confirmation
        return add_source_wizard.confirm()

    @record_action
    def open_add_source(self) -> SelectSourceTypeForm:
        create_source_button = "button[data-ouia-component-id=add_source]"
        self._driver.click(create_source_button)
        return self._new_page(SelectSourceTypeForm)

    @creates_toast
    @record_action
    def trigger_scan(self, data: TriggerScanDTO) -> SourcesMainPage:
        item: SourceListElem = self._get_item(data.source_name)
        popup = item.open_scan()
        popup.fill(data.scan_form)
        return popup.confirm()
