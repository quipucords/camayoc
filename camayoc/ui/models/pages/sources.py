from __future__ import annotations

from typing import overload

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
from camayoc.ui.enums import Pages
from camayoc.ui.enums import SourceTypes
from camayoc.ui.types import AddSourceDTO
from camayoc.ui.types import NetworkSourceFormDTO
from camayoc.ui.types import NewScanFormDTO
from camayoc.ui.types import SatelliteSourceFormDTO
from camayoc.ui.types import SelectSourceDTO
from camayoc.ui.types import TriggerScanDTO
from camayoc.ui.types import VCenterSourceFormDTO


class SelectSourceTypeForm(Form, WizardStep, AbstractPage):
    NEXT_STEP_RESULT_CLASS = None
    PREV_STEP_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = None

    class FormDefinition:
        source_type = RadioGroupField("div.wizard-pf-contents:not(.hidden)")

    def fill(self, data: SelectSourceDTO):
        source_type_map = {
            SourceTypes.NETWORK_RANGE: NetworkRangeSourceCredentialsForm,
            SourceTypes.SATELLITE: SatelliteSourceCredentialsForm,
            SourceTypes.VCENTER_SERVER: VCenterSourceCredentialsForm,
        }
        next_step_class = source_type_map.get(data.source_type)
        setattr(self, "NEXT_STEP_RESULT_CLASS", next_step_class)
        super().fill(data)


class SourceCredentialsForm(Form, WizardStep, AbstractPage):
    NEXT_STEP_LOCATOR = '.modal-footer button:has-text("Save")'
    NEXT_STEP_RESULT_CLASS = Pages.SOURCES_RESULTS_PAGE
    PREV_STEP_RESULT_CLASS = SelectSourceTypeForm


class NetworkRangeSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField('label:has-text("Name") + div input')
        addresses = InputField(
            'label:has-text("Search addresses") + div textarea',
            transform_input=lambda i: ",".join(i),
        )
        port = InputField('label:has-text("Port") + div input', transform_input=lambda i: str(i))
        credentials = MultipleSelectField("button#credentials")
        use_paramiko = CheckboxField('label:has-text("Paramiko") input')

    @overload
    def fill(self, data: NetworkSourceFormDTO):
        ...

    def fill(self, data: NetworkSourceFormDTO):
        super().fill(data)


class SatelliteSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField('label:has-text("Name") + div input')
        address = InputField('label:has-text("IP address") + div input')
        credentials = MultipleSelectField("button#credentials")
        connection = SelectField("button#optionSslProtocol")
        verify_ssl = CheckboxField('label:has-text("Verify SSL") input')

    @overload
    def fill(self, data: SatelliteSourceFormDTO):
        ...

    def fill(self, data: SatelliteSourceFormDTO):
        super().fill(data)


class VCenterSourceCredentialsForm(SourceCredentialsForm):
    class FormDefinition:
        source_name = InputField('label:has-text("Name") + div input')
        address = InputField('label:has-text("IP address") + div input')
        credentials = MultipleSelectField("button#credentials")
        connection = SelectField("button#optionSslProtocol")
        verify_ssl = CheckboxField('label:has-text("Verify SSL") input')

    @overload
    def fill(self, data: VCenterSourceFormDTO):
        ...

    def fill(self, data: VCenterSourceFormDTO):
        super().fill(data)


class ResultForm(WizardStep, AbstractPage):
    NEXT_STEP_LOCATOR = ".modal-footer button.btn-primary"
    NEXT_STEP_RESULT_CLASS = Pages.SOURCES


class ScanForm(Form, PopUp, AbstractPage):
    SAVE_RESULT_CLASS = Pages.SOURCES
    CANCEL_RESULT_CLASS = Pages.SOURCES

    class FormDefinition:
        scan_name = InputField("input[name=scanName]")
        max_concurrent_scans = InputField("input#scanConcurrency")
        jboss_eap = CheckboxField("input[name=jbossEap]")
        fuse = CheckboxField("input[name=jbossFuse]")
        jboss_web_server = CheckboxField("input[name=jbossWs]")
        decision_manager = CheckboxField("input[name=jbossBrms]")
        alternate_dirs = InputField("textarea[name=displayScanDirectories]")

    @overload
    def fill(self, data: NewScanFormDTO):
        ...

    def fill(self, data: NewScanFormDTO):
        super().fill(data)


class SourceListElem(AbstractListItem):
    def open_scan(self) -> ScanForm:
        scan_locator = 'div.list-view-pf-actions button:has-text("Scan")'
        self.locator.locator(scan_locator).click()
        return ScanForm(client=self._client)


class SourcesMainPage(MainPageMixin):
    ITEM_CLASS = SourceListElem

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

    def open_add_source(self) -> SelectSourceTypeForm:
        create_source_button = 'button.btn-primary:has-text("Add")'
        self._driver.click(create_source_button)
        return self._new_page(SelectSourceTypeForm)

    def trigger_scan(self, data: TriggerScanDTO) -> SourcesMainPage:
        item: SourceListElem = self._get_item(data.source_name)
        popup = item.open_scan()
        popup.fill(data.scan_form)
        return popup.confirm()
