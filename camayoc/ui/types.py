from __future__ import annotations

from dataclasses import dataclass
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

from .enums import CredentialTypes
from .enums import NetworkCredentialAuthenticationTypes
from .enums import NetworkCredentialBecomeMethods
from .enums import SourceConnectionTypes
from .enums import SourceTypes

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

    def _new_page(self, class_or_page) -> UIPage:
        ...


class UIListItem(Protocol):
    locator: Locator
    _client: Client


class UIField(Protocol):
    locator: str
    transform_input: Optional[Callable]
    parent: UIPage
    name: str
    driver: Page

    def bind(self, parent, name, driver: Page) -> None:
        ...

    def fill(self, value) -> None:
        ...


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


@frozen
class SSHNetworkCredentialFormDTO(_NetworkCredentialFormDTO):
    authentication_type: NetworkCredentialAuthenticationTypes = (
        NetworkCredentialAuthenticationTypes.SSH_KEY
    )
    ssh_key_file: str = field(kw_only=True)
    passphrase: Optional[str] = None


NetworkCredentialFormDTO = Union[
    PlainNetworkCredentialFormDTO,
    SSHNetworkCredentialFormDTO,
]


@frozen
class SatelliteCredentialFormDTO:
    credential_name: str
    username: str
    password: str


@frozen
class VCenterCredentialFormDTO:
    credential_name: str
    username: str
    password: str


CredentialFormDTO = Union[
    NetworkCredentialFormDTO, SatelliteCredentialFormDTO, VCenterCredentialFormDTO
]


@frozen
class AddCredentialDTO:
    credential_type: CredentialTypes
    credential_form_dto: CredentialFormDTO


@frozen
class SelectSourceDTO:
    source_type: SourceTypes


@frozen
class NetworkSourceFormDTO:
    source_name: str
    addresses: list[str]
    credentials: list[str]
    port: Optional[int] = None
    use_paramiko: Optional[bool] = None


@frozen
class SatelliteSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    connection: SourceConnectionTypes
    verify_ssl: Optional[bool] = None


@frozen
class VCenterSourceFormDTO:
    source_name: str
    address: str
    credentials: list[str]
    connection: SourceConnectionTypes
    verify_ssl: Optional[bool] = None


SourceFormDTO = Union[
    NetworkSourceFormDTO,
    SatelliteSourceFormDTO,
    VCenterSourceFormDTO,
]


@frozen
class AddSourceDTO:
    select_source_type: SelectSourceDTO
    source_form: SourceFormDTO


@frozen
class NewScanFormDTO:
    scan_name: str
    max_concurrent_scans: Optional[int] = None
    jboss_eap: Optional[bool] = None
    fuse: Optional[bool] = None
    jboss_web_server: Optional[bool] = None
    decision_manager: Optional[bool] = None
    alternate_dirs: Optional[str] = None


@frozen
class TriggerScanDTO:
    source_name: str
    scan_form: NewScanFormDTO
