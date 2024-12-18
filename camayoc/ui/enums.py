from enum import Enum
from enum import auto


class StrEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.capitalize()


class LowercasedStrEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class Pages(StrEnum):
    CREDENTIALS = "credentials.CredentialsMainPage"
    LOGIN = "login.Login"
    SCANS = "scans.ScansMainPage"
    SOURCES = "sources.SourcesMainPage"


class MainMenuPages(StrEnum):
    SOURCES = auto()
    SCANS = auto()
    CREDENTIALS = auto()


class CredentialTypes(StrEnum):
    NETWORK = auto()
    SATELLITE = auto()
    VCENTER = auto()
    OPENSHIFT = auto()
    ANSIBLE = auto()
    RHACS = auto()


class NetworkCredentialAuthenticationTypes(StrEnum):
    USERNAME_AND_PASSWORD = "Username and Password"
    SSH_KEY = "SSH Key"


class NetworkCredentialBecomeMethods(LowercasedStrEnum):
    SUDO = auto()
    SU = auto()
    PBRUN = auto()
    PFEXEC = auto()
    DOAS = auto()
    DZDO = auto()
    KSU = auto()
    RUNAS = auto()


class OpenShiftCredentialAuthenticationTypes(StrEnum):
    USERNAME_AND_PASSWORD = "Username and Password"
    TOKEN = "Token"


class SourceTypes(StrEnum):
    NETWORK_RANGE = "network"
    SATELLITE = "satellite"
    VCENTER_SERVER = "vcenter"
    OPENSHIFT = "openshift"
    ANSIBLE_CONTROLLER = "ansible"
    RHACS = "rhacs"


class SourceConnectionTypes(StrEnum):
    SSL23 = "SSLv23"
    TLS1 = "TLSv1"
    TLS11 = "TLSv1.1"
    TLS12 = "TLSv1.2"
    DISABLE = "Disable SSL"


class ScansPopupTableColumns(StrEnum):
    SCAN_TIME = "header_scan_time"
    SCAN_RESULT = "header_scan_result"


class ColumnOrdering(StrEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
