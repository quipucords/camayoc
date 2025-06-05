from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Optional
from typing import Protocol
from typing import Sequence
from typing import Union

from attrs import field
from attrs import frozen
from playwright.sync_api import Locator
from playwright.sync_api import Page

from camayoc.qpc_models import Credential
from camayoc.qpc_models import Source
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import NetworkCredentialAuthenticationTypes
from camayoc.ui.enums import NetworkCredentialBecomeMethods
from camayoc.ui.enums import OpenShiftCredentialAuthenticationTypes
from camayoc.ui.enums import SourceConnectionTypes
from camayoc.ui.enums import SourceTypes

if TYPE_CHECKING:
    from camayoc.ui import Client


@dataclass(frozen=True)
class HistoryRecord:
    start_page: str
    action: str
    args: Sequence[Any]
    kwargs: Sequence[Any]
    end_page: str


class Session(Protocol):
    history: list[HistoryRecord]

    def last_record(self) -> Optional[HistoryRecord]:
        pass

    def add_record(self, record: HistoryRecord) -> None:
        pass


class UIPage(Protocol):
    _client: Client
    _driver: Page

    def _new_page(self, class_or_page) -> UIPage: ...


class UIListItem(Protocol):
    locator: Locator
    _client: Client


class UIField(Protocol):
    locator: str
    transform_input: Optional[Callable]
    parent: UIPage
    name: str
    driver: Page

    def bind(self, parent, name, driver: Page) -> None: ...

    def fill(self, value) -> None: ...


@frozen
class LoginFormDTO:
    username: Optional[str] = None
    password: Optional[str] = None


@frozen
class _NetworkCredentialFormDTO:
    credential_name: str
    username: str
    become_method: NetworkCredentialBecomeMethods
    become_user: Optional[str] = None
    become_password: Optional[str] = None


@frozen
class PlainNetworkCredentialFormDTO(_NetworkCredentialFormDTO):
    authentication_type: NetworkCredentialAuthenticationTypes = (
        NetworkCredentialAuthenticationTypes.USERNAME_AND_PASSWORD
    )
    password: str = field(kw_only=True)

    @classmethod
    def from_model(cls, model: Credential):
        try:
            become_method_name = getattr(model, "become_method")
            become_method = getattr(NetworkCredentialBecomeMethods, become_method_name.upper())
        except AttributeError:
            become_method = next(iter(NetworkCredentialBecomeMethods))

        return cls(
            credential_name=model.name,
            username=model.username,
            password=model.password,
            become_method=become_method,
            become_user=getattr(model, "become_user", None),
            become_password=getattr(model, "become_password", None),
        )


@frozen
class SSHNetworkCredentialFormDTO(_NetworkCredentialFormDTO):
    authentication_type: NetworkCredentialAuthenticationTypes = (
        NetworkCredentialAuthenticationTypes.SSH_KEY
    )
    ssh_key_file: str = field(kw_only=True)
    passphrase: Optional[str] = None

    @classmethod
    def from_model(cls, model: Credential):
        try:
            become_method_name = getattr(model, "become_method")
            become_method = getattr(NetworkCredentialBecomeMethods, become_method_name.upper())
        except AttributeError:
            become_method = next(iter(NetworkCredentialBecomeMethods))

        return cls(
            credential_name=model.name,
            username=model.username,
            ssh_key_file=model.ssh_key,
            passphrase=model.auth_token,
            become_method=become_method,
            become_user=getattr(model, "become_user", None),
            become_password=getattr(model, "become_password", None),
        )

    def to_model(self):
        model = Credential(
            cred_type="network",
            name=self.credential_name,
            username=self.username,
            ssh_key=self.ssh_key_file,
            auth_token=self.passphrase,
            become_method=self.become_method.value,
            become_user=self.become_user,
            become_password=self.become_password,
        )
        return model


NetworkCredentialFormDTO = Union[
    PlainNetworkCredentialFormDTO,
    SSHNetworkCredentialFormDTO,
]


@frozen
class SatelliteCredentialFormDTO:
    credential_name: str
    username: str
    password: str

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, username=model.username, password=model.password)

    def to_model(self):
        model = Credential(
            cred_type="satellite",
            name=self.credential_name,
            username=self.username,
            password=self.password,
        )
        return model


@frozen
class VCenterCredentialFormDTO:
    credential_name: str
    username: str
    password: str

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, username=model.username, password=model.password)

    def to_model(self):
        model = Credential(
            cred_type="vcenter",
            name=self.credential_name,
            username=self.username,
            password=self.password,
        )
        return model


@frozen
class PlainOpenShiftCredentialFormDTO:
    credential_name: str
    username: str
    password: str
    authentication_type: OpenShiftCredentialAuthenticationTypes = (
        OpenShiftCredentialAuthenticationTypes.USERNAME_AND_PASSWORD
    )

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, username=model.username, password=model.password)

    def to_model(self):
        model = Credential(
            cred_type="openshift",
            name=self.credential_name,
            username=self.username,
            password=self.password,
        )
        return model


@frozen
class TokenOpenShiftCredentialFormDTO:
    credential_name: str
    token: str
    authentication_type: OpenShiftCredentialAuthenticationTypes = (
        OpenShiftCredentialAuthenticationTypes.TOKEN
    )

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, token=model.auth_token)

    def to_model(self):
        model = Credential(
            cred_type="openshift",
            name=self.credential_name,
            auth_token=self.token,
        )
        return model


OpenShiftCredentialFormDTO = Union[
    PlainOpenShiftCredentialFormDTO,
    TokenOpenShiftCredentialFormDTO,
]


@frozen
class AnsibleCredentialFormDTO:
    credential_name: str
    username: str
    password: str

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, username=model.username, password=model.password)

    def to_model(self):
        model = Credential(
            cred_type="ansible",
            name=self.credential_name,
            username=self.username,
            password=self.password,
        )
        return model


@frozen
class RHACSCredentialFormDTO:
    credential_name: str
    token: str

    @classmethod
    def from_model(cls, model: Credential):
        return cls(credential_name=model.name, token=model.auth_token)

    def to_model(self):
        model = Credential(
            cred_type="rhacs",
            name=self.credential_name,
            auth_token=self.token,
        )
        return model


CredentialFormDTO = Union[
    NetworkCredentialFormDTO,
    SatelliteCredentialFormDTO,
    VCenterCredentialFormDTO,
    OpenShiftCredentialFormDTO,
    AnsibleCredentialFormDTO,
    RHACSCredentialFormDTO,
]


@frozen
class AddCredentialDTO:
    credential_type: CredentialTypes
    credential_form: CredentialFormDTO

    @classmethod
    def from_model(cls, model: Credential):
        match model.cred_type:
            case "network":
                credential_type = CredentialTypes.NETWORK
                dto_cls = PlainNetworkCredentialFormDTO
                if model.ssh_key:
                    dto_cls = SSHNetworkCredentialFormDTO
                credential_form_dto = dto_cls.from_model(model)
            case "satellite":
                credential_type = CredentialTypes.SATELLITE
                credential_form_dto = SatelliteCredentialFormDTO.from_model(model)
            case "vcenter":
                credential_type = CredentialTypes.VCENTER
                credential_form_dto = VCenterCredentialFormDTO.from_model(model)
            case "openshift":
                credential_type = CredentialTypes.OPENSHIFT
                credential_form_dto = OpenShiftCredentialFormDTO.from_model(model)
            case "ansible":
                credential_type = CredentialTypes.ANSIBLE
                credential_form_dto = AnsibleCredentialFormDTO.from_model(model)
            case "rhacs":
                credential_type = CredentialTypes.RHACS
                credential_form_dto = RHACSCredentialFormDTO.from_model(model)
            case _:
                raise ValueError(f"Can't create Credential UI DTO from {model}")
        return cls(credential_type, credential_form_dto)


@frozen
class NetworkSourceFormDTO:
    source_name: str
    addresses: list[str]
    credentials: list[str]
    port: Optional[int] = None
    use_paramiko: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        return cls(
            source_name=model.name,
            addresses=model.hosts,
            credentials=model.credentials,
            port=getattr(model, "port", None),
        )


@frozen
class SatelliteSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    port: Optional[str] = None
    connection: Optional[SourceConnectionTypes] = None
    verify_ssl: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        port_args = {}
        if hasattr(model, "port") and model.port:
            port_args["port"] = str(model.port)
        return cls(
            source_name=model.name,
            address=model.hosts[0],
            credentials=model.credentials,
            verify_ssl=model.options.get("ssl_cert_verify"),
            **port_args,
        )


@frozen
class VCenterSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    port: Optional[str] = None
    connection: Optional[SourceConnectionTypes] = None
    verify_ssl: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        port_args = {}
        if hasattr(model, "port") and model.port:
            port_args["port"] = str(model.port)
        return cls(
            source_name=model.name,
            address=model.hosts[0],
            credentials=model.credentials,
            verify_ssl=model.options.get("ssl_cert_verify"),
            **port_args,
        )


@frozen
class OpenShiftSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    port: Optional[str] = None
    connection: Optional[SourceConnectionTypes] = None
    verify_ssl: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        port_args = {}
        if hasattr(model, "port") and model.port:
            port_args["port"] = str(model.port)
        return cls(
            source_name=model.name,
            address=model.hosts[0],
            credentials=model.credentials,
            verify_ssl=model.options.get("ssl_cert_verify"),
            **port_args,
        )


@frozen
class AnsibleSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    port: Optional[str] = None
    connection: Optional[SourceConnectionTypes] = None
    verify_ssl: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        port_args = {}
        if hasattr(model, "port") and model.port:
            port_args["port"] = str(model.port)
        return cls(
            source_name=model.name,
            address=model.hosts[0],
            credentials=model.credentials,
            verify_ssl=model.options.get("ssl_cert_verify"),
            **port_args,
        )


@frozen
class RHACSSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    port: Optional[str] = None
    connection: Optional[SourceConnectionTypes] = None
    verify_ssl: Optional[bool] = None

    @classmethod
    def from_model(cls, model: Source):
        port_args = {}
        if hasattr(model, "port") and model.port:
            port_args["port"] = str(model.port)
        return cls(
            source_name=model.name,
            address=model.hosts[0],
            credentials=model.credentials,
            verify_ssl=model.options.get("ssl_cert_verify"),
            **port_args,
        )


SourceFormDTO = Union[
    NetworkSourceFormDTO,
    SatelliteSourceFormDTO,
    VCenterSourceFormDTO,
    OpenShiftSourceFormDTO,
    AnsibleSourceFormDTO,
    RHACSSourceFormDTO,
]


@frozen
class AddSourceDTO:
    source_type: SourceTypes
    source_form: SourceFormDTO

    @classmethod
    def from_model(cls, model: Source):
        match model.source_type:
            case "network":
                source_type = SourceTypes.NETWORK_RANGE
                source_form_dto = NetworkSourceFormDTO.from_model(model)
            case "satellite":
                source_type = SourceTypes.SATELLITE
                source_form_dto = SatelliteSourceFormDTO.from_model(model)
            case "vcenter":
                source_type = SourceTypes.VCENTER_SERVER
                source_form_dto = VCenterSourceFormDTO.from_model(model)
            case "openshift":
                source_type = SourceTypes.OPENSHIFT
                source_form_dto = OpenShiftSourceFormDTO.from_model(model)
            case "ansible":
                source_type = SourceTypes.ANSIBLE_CONTROLLER
                source_form_dto = AnsibleSourceFormDTO.from_model(model)
            case "rhacs":
                source_type = SourceTypes.RHACS
                source_form_dto = RHACSSourceFormDTO.from_model(model)
            case _:
                raise ValueError(f"Can't create Source UI DTO from {model}")
        return cls(source_type, source_form_dto)


@frozen
class NewScanFormDTO:
    scan_name: str
    max_concurrent_scans: Optional[int] = None
    jboss_eap: Optional[bool] = None
    fuse: Optional[bool] = None
    jboss_web_server: Optional[bool] = None
    alternate_dirs: Optional[str] = None


@frozen
class TriggerScanDTO:
    source_name: str
    scan_form: NewScanFormDTO


@frozen
class SummaryReportDataPoint:
    key: str
    label: str
    value: str
    parsed_value: Any


SummaryReportData = MappingProxyType[str, SummaryReportDataPoint]
