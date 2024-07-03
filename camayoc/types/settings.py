from typing import Any
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from typing_extensions import Annotated


class CamayocOptions(BaseModel):
    run_scans: Optional[bool] = False
    scan_timeout: Optional[int] = 600


class QuipucordsServerOptions(BaseModel):
    hostname: str
    https: Optional[bool] = False
    port: Optional[int] = 8000
    # FIXME: this is thin layer around requests.adapters.BaseAdapter.send() `verify`
    # param, which can be a boolean OR string (representing local path to CA bundle)
    ssl_verify: Optional[bool] = False
    username: str
    password: str
    ssh_keyfile_path: str


class QuipucordsCLIOptions(BaseModel):
    executable: Optional[str] = "qpc"
    display_name: Optional[str] = "qpc"


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


class PlainOpenShiftCredentialOptions(BaseModel):
    name: str
    type: Literal["openshift"]
    username: str
    password: str


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
    PlainOpenShiftCredentialOptions,
    ServicesCredentialOptions,
]


class SourceOptionsOptions(BaseModel):
    ssl_cert_verify: Optional[bool] = True


class SourceOptions(BaseModel):
    name: str
    type: str
    hosts: list[str]
    port: Optional[int] = None
    credentials: list[str]
    options: Optional[SourceOptionsOptions] = None


class ExpectedDistributionData(BaseModel):
    name: str
    version: str
    release: str
    is_redhat: bool


class ExpectedProductData(BaseModel):
    name: str
    presence: str


class ExpectedOpenShiftData(BaseModel):
    cluster_id: str
    version: str
    nodes: list[str]
    operators: list[str]


class ExpectedScanData(BaseModel):
    distribution: Optional[ExpectedDistributionData] = None
    products: Optional[list[ExpectedProductData]] = None
    cluster_info: Optional[ExpectedOpenShiftData] = None
    installed_products: Optional[list[str]] = None
    raw_facts: Optional[dict[str, Any]] = None


class ScanOptions(BaseModel):
    name: str
    sources: list[str]
    expected_data: Optional[dict[str, ExpectedScanData]] = None


class Configuration(BaseModel):
    camayoc: CamayocOptions
    quipucords_server: QuipucordsServerOptions
    quipucords_cli: QuipucordsCLIOptions
    credentials: list[CredentialOptions]
    sources: list[SourceOptions]
    scans: list[ScanOptions]

    @model_validator(mode="before")
    @classmethod
    def check_name_uniqueness(cls, values: Any) -> Any:
        if isinstance(values, dict):
            for option in ("credentials", "sources", "scans"):
                names = [item.get("name") for item in values.get(option)]
                if len(names) != len(set(names)):
                    msg = f"Names inside '{option}' are not unique"
                    raise ValueError(msg)
        return values

    @model_validator(mode="before")
    @classmethod
    def check_credentials(cls, values: Any) -> Any:
        if isinstance(values, dict):
            credentials = {cred.get("name"): cred for cred in values.get("credentials")}
            for source in values.get("sources"):
                for cred_name in source.get("credentials"):
                    if cred_name not in credentials:
                        source_name = source.get("name")
                        msg = f"Source '{source_name}' refers to undefined credential '{cred_name}'"
                        raise ValueError(msg)
                    cred = credentials.get(cred_name)

                    source_type = source.get("type")
                    cred_type = cred.get("type")
                    if source_type != cred_type:
                        source_name = source.get("name")
                        msg = (
                            f"Source '{source_name}' type {source_type}"
                            f" does not match credential '{cred_name}' type {cred_type}"
                        )
                        raise ValueError(msg)
        return values

    @model_validator(mode="before")
    @classmethod
    def check_sources(cls, values: Any) -> Any:
        if isinstance(values, dict):
            source_names = [source.get("name") for source in values.get("sources")]
            for scan in values.get("scans"):
                for source_name in scan.get("sources"):
                    if source_name not in source_names:
                        scan_name = scan.get("name")
                        msg = f"Scan '{scan_name}' refers to undefined source '{source_name}'"
                        raise ValueError(msg)
        return values
