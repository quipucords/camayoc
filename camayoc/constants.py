# coding=utf-8
"""Values usable by multiple test modules."""

from camayoc import utils

DBSERIALIZER_CREDENTIALS_FILE_PATH = "credentials.json"
"""Path to file that stores serialized credentials data, relative to main serializer destination."""

DBSERIALIZER_SOURCES_FILE_PATH = "sources.json"
"""Path to file that stores serialized sources data, relative to main serializer destination."""

DBSERIALIZER_SCANS_FILE_PATH = "scans.json"
"""Path to file that stores serialized scans data, relative to main serializer destination."""

DBSERIALIZER_CONNECTIONJOBS_DIR_PATH = "jobs"
"""Path to directory that stores job connections data, relative to main serializer destination."""

DBSERIALIZER_SCANJOBS_DIR_PATH = "scans"
"""Path to directory that stores scan jobs data, relative to main serializer destination."""

DBSERIALIZER_REPORTS_DIR_PATH = "reports"
"""Path to directory that stores reports, relative to main serializer destination.

Each report is represented by directory named after report id. Only details.json
and aggregate.json are stored."""

CLI_DEBUG_MSG = "Executing command: %s"
"""Message to log when executing command through CLI."""

VALID_BOOLEAN_CHOICES = ["true", "false"]
"""Valid qpc/dsc CLI boolean choices."""

VALID_SSL_PROTOCOLS = ["SSLv23", "TLSv1", "TLSv1_1", "TLSv1_2"]
"""Valid qpc/dsc CLI SSL protocol choices."""

MASKED_PASSWORD_OUTPUT = r"\*{8}"
"""Regex that matches password on outputs."""

MASKED_AUTH_TOKEN_OUTPUT = r"\*{8}"
"""Regex that matches auth_token on outputs."""

AUTH_TOKEN_INPUT = "Provide a token for authentication.\r\nToken:"
"""Connection auth_token input prompt."""

BECOME_PASSWORD_INPUT = (
    "Provide a privilege escalation password to be used when running a network scan.\r\nPassword:"
)
"""Become password input prompt."""

CONNECTION_PASSWORD_INPUT = "Provide( a)? connection password.\r\nPassword:"
"""Connection password input prompt."""

SUDO_PASSWORD_INPUT = "Provide password for sudo.\r\nPassword:"
"""Sudo password input prompt."""

VAULT_PASSWORD = utils.uuid4()
"""Vault password will be unique across Python sessions."""

QPC_API_ROOT = "api/"
"""The root path to access the QPC server API."""

QPC_CREDENTIALS_PATH = "v2/credentials/"
"""The path to the credentials endpoint for CRUD tasks."""

QPC_SOURCE_PATH = "v2/sources/"
"""The path to the profiles endpoint for CRUD tasks."""

QPC_SCAN_PATH = "v1/scans/"
"""The path to the scans endpoint for CRUD tasks."""

QPC_SCANJOB_PATH = "v1/jobs/"
"""The path to the scanjob endpoint for CRUD tasks."""

QPC_REPORTS_PATH = "v1/reports/"
"""The path to the endpoint used for obtaining reports."""

QPC_SCAN_TERMINAL_STATES = ("completed", "failed", "canceled")
"""Scans to not change from these states without intervention."""

QPC_SCAN_STATES = QPC_SCAN_TERMINAL_STATES + ("running",)
"""All the states that a quipucords scan can take."""

QPC_TOKEN_PATH = "v1/token/"
"""The path to the endpoint used for obtaining an authentication token."""

QPC_API_INVALID_TOKEN_MESSAGE = "'Invalid token'"
"""String that will be in API response when request token is invalid."""

QPC_LOGOUT_PATH = "v1/users/logout/"
"""The path to the endpoint used to log user out."""

QPC_CURRENT_USER_PATH = "v1/users/current/"
"""The path to the endpoint that has information about current user."""

QPC_SOURCE_TYPES = (
    "vcenter",
    "network",
    "satellite",
    "openshift",
    "ansible",
)
"""Types of sources that the quipucords server supports."""

QPC_SOURCES_DEFAULT_PORT = {
    "network": 22,
    "vcenter": 443,
    "satellite": 443,
    "openshift": 6443,
    "ansible": 443,
}
"""Default sources port that the quipucords server supports."""

QPC_SCAN_TYPES = ("inspect",)
"""Types of scans that the quipucords server supports."""

QPC_HOST_MANAGER_TYPES = ("vcenter", "satellite", "openshift", "ansible")
"""Types of host managers that the quipucords server supports."""

QPC_BECOME_METHODS = ("doas", "dzdo", "ksu", "pbrun", "pfexec", "runas", "su", "sudo")
"""Supported become methods for quipucords server."""

QPC_OPTIONAL_PRODUCTS = ("jboss_eap", "jboss_fuse", "jboss_ws")
"""Optional products that can be enabled or disabled for a scan."""

SOURCE_TYPES_WITH_LIGHTSPEED_SUPPORT = (
    "vcenter",
    "network",
    "satellite",
)
"""Types of sources that can generate lightspeed reports."""
