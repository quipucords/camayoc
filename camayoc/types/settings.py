from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import root_validator
from typing_extensions import Annotated


class CamayocOptions(BaseModel):
    run_scans: Optional[bool] = False


class QuipucordsServerOptions(BaseModel):
    hostname: str
    https: Optional[bool] = False
    port: Optional[int] = 8000
    ssl_verify: Optional[bool] = Field(False, alias="ssl-verify")
    username: str
    password: str
    ssh_keyfile_path: str


class QuipucordsCLIOptions(BaseModel):
    executable: Optional[str] = "qpc"
    display_name: Optional[str] = "qpc"


class OpenShiftOptions(BaseModel):
    hostname: str
    port: int
    token: str
    skip_tls_verify: bool
    cluster_id: str
    version: str
    nodes: list[str]
    operators: list[str]


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


class OpenShiftCredentialOptions(BaseModel):
    name: str
    type: Literal["openshift"]
    auth_token: str


class RHACSCredentialOptions(BaseModel):
    name: str
    type: Literal["rhacs"]
    auth_token: str


class AnsibleCredentialOptions(BaseModel):
    name: str
    type: Literal["ansible"]
    username: str
    password: str


ServicesCredentialOptions = Annotated[
    Union[
        VCenterCredentialOptions,
        SatelliteCredentialOptions,
        OpenShiftCredentialOptions,
        RHACSCredentialOptions,
        AnsibleCredentialOptions,
    ],
    Field(discriminator="type"),
]


CredentialOptions = Union[
    PlainNetworkCredentialOptions,
    SSHNetworkCredentialOptions,
    ServicesCredentialOptions,
]


class SourceOptionsOptions(BaseModel):
    ssl_cert_verify: Optional[bool] = True


class SourceOptions(BaseModel):
    name: str
    type: str
    hosts: list[str]
    credentials: list[str]
    options: Optional[SourceOptionsOptions]


class ExpectedDistributionData(BaseModel):
    name: str
    version: str
    release: str


class ExpectedProductData(BaseModel):
    name: str
    presence: str


class ExpectedScanData(BaseModel):
    distribution: Optional[ExpectedDistributionData]
    products: Optional[list[ExpectedProductData]]


class ScanOptions(BaseModel):
    name: str
    sources: list[str]
    expected_data: Optional[dict[str, ExpectedScanData]]


class Configuration(BaseModel):
    camayoc: CamayocOptions
    quipucords_server: QuipucordsServerOptions
    quipucords_cli: QuipucordsCLIOptions
    openshift: list[OpenShiftOptions]
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
                    msg = (
                        f"Source '{source.name}' type {source.type}"
                        f" does not match credential '{cred.name}' type {cred.type}"
                    )
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
