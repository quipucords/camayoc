from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import root_validator
from typing_extensions import Annotated


class QuipucordsServerOptions(BaseModel):
    hostname: str
    https: Optional[bool] = False
    port: Optional[int] = 8000
    ssl_verify: Optional[bool] = Field(False, alias="ssl-verify")
    username: str
    password: str
    ssh_keyfile_path: str


class OpenShiftOptions(BaseModel):
    hostname: str
    token: str
    skip_tls_verify: bool


class VCenterOptions(BaseModel):
    hostname: str
    password: str
    username: str


class PlainNetworkCredentialOptions(BaseModel):
    name: str
    type: Literal["network"]
    username: str
    password: str
    become_method: Optional[str] = None  # FIXME: should be enum
    become_user: Optional[str] = None
    become_password: Optional[str] = None


class SSHNetworkCredentialOptions(BaseModel):
    name: str
    type: Literal["network"]
    username: str
    sshkeyfile: str
    passphrase: Optional[str] = None
    become_method: Optional[str] = None  # FIXME: should be enum
    become_user: Optional[str] = None
    become_password: Optional[str] = None


class SatelliteCredentialOptions(BaseModel):
    name: str
    type: Literal["satellite"]
    username: str
    password: str


class VCenterCredentialOptions(BaseModel):
    name: str
    type: Literal["vcenter"]
    username: str
    password: str


CredentialOptions = Annotated[
    Union[
        PlainNetworkCredentialOptions,
        SSHNetworkCredentialOptions,
        SatelliteCredentialOptions,
        VCenterCredentialOptions,
    ],
    Field(discriminator="type"),
]


class SourceOptionsOptions(BaseModel):
    ssl_cert_verify: Optional[bool] = True


class SourceOptions(BaseModel):
    name: str
    type: str
    hosts: list[str]
    credentials: list[str]
    options: Optional[SourceOptionsOptions]


class ExpectedScanData(BaseModel):
    hostname: str
    credentials: list[str]
    ipv4: str
    hypervisor: str  # FIXME: should be enum
    distribution: dict[str, str]  # FIXME: should be strongly-types
    products: dict[str, dict[str, str]]  # FIXME: should be strongly-types


class ScanOptions(BaseModel):
    name: str
    sources: list[str]
    expected_data: Optional[list[ExpectedScanData]]


class Configuration(BaseModel):
    quipucords_server: QuipucordsServerOptions
    openshift: OpenShiftOptions
    vcenter: VCenterOptions
    credentials: list[CredentialOptions]
    sources: list[SourceOptions]
    scans: list[ScanOptions]

    @root_validator
    def check_name_uniqueness(cls, values):
        for option in ("credentials", "sources", "scans"):
            names = [item.name for item in values.get(option)]
            if len(names) != len(set(names)):
                msg = f"Names inside '{option}' are not unique"
                raise ValueError(msg)
        return values

    @root_validator
    def check_credentials(cls, values):
        credentials = {cred.name: cred for cred in values.get("credentials")}
        for source in values.get("sources"):
            for cred_name in source.credentials:
                if cred_name not in credentials:
                    msg = f"Source '{source.name}' refers to undefined credential '{cred_name}'"
                    raise ValueError(msg)
                cred = credentials.get(cred_name)
                if source.type != cred.type:
                    msg = f"Source '{source.name}' type {source.type} does not match credential '{cred.name}' type {cred.type}"
                    raise ValueError(msg)
        return values

    @root_validator
    def check_sources(cls, values):
        source_names = [source.name for source in values.get("sources")]
        for scan in values.get("scans"):
            for source_name in scan.sources:
                if source_name not in source_names:
                    msg = f"Scan '{scan.name}' refers to undefined source '{source_name}'"
                    raise ValueError(msg)
        return values
