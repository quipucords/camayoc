# coding=utf-8
"""Values usable by multiple test modules."""
from camayoc import utils

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
    "Provide a privilege escalation password to be used when running a "
    "network scan.\r\nPassword:"
)
"""Become password input prompt."""

CONNECTION_PASSWORD_INPUT = "Provide( a)? connection password.\r\nPassword:"
"""Connection password input prompt."""

SUDO_PASSWORD_INPUT = "Provide password for sudo.\r\nPassword:"
"""Sudo password input prompt."""

VAULT_PASSWORD = utils.uuid4()
"""Vault password will be unique across Python sessions."""

QPC_API_VERSION = "api/v1/"
"""The root path to access the QPC server API."""

QPC_CREDENTIALS_PATH = "credentials/"
"""The path to the credentials endpoint for CRUD tasks."""

QPC_SOURCE_PATH = "sources/"
"""The path to the profiles endpoint for CRUD tasks."""

QPC_SCAN_PATH = "scans/"
"""The path to the scans endpoint for CRUD tasks."""

QPC_SCANJOB_PATH = "jobs/"
"""The path to the scanjob endpoint for CRUD tasks."""

QPC_REPORTS_PATH = "reports/"
"""The path to the endpoint used for obtaining reports."""

QPC_SCAN_TERMINAL_STATES = ("completed", "failed", "paused", "canceled")
"""Scans to not change from these states without intervention."""

QPC_SCAN_STATES = QPC_SCAN_TERMINAL_STATES + ("running",)
"""All the states that a quipucords scan can take."""

QPC_TOKEN_PATH = "token/"
"""The path to the endpoint used for obtaining an authentication token."""

QPC_SOURCE_TYPES = (
    "vcenter",
    "network",
    "satellite",
    "openshift",
)
"""Types of sources that the quipucords server supports."""

QPC_SOURCES_DEFAULT_PORT = {
    "network": 22,
    "vcenter": 443,
    "satellite": 443,
    "openshift": 6443,
}
"""Default sources port that the quipucords server supports."""

QPC_SCAN_TYPES = ("inspect", "connect")
"""Types of scans that the quipucords server supports."""

QPC_HOST_MANAGER_TYPES = ("vcenter", "satellite", "openshift")
"""Types of host managers that the quipucords server supports."""

QPC_BECOME_METHODS = ("doas", "dzdo", "ksu", "pbrun", "pfexec", "runas", "su", "sudo")
"""Supported become methods for quipucords server."""

QPC_OPTIONAL_PRODUCTS = ("jboss_brms", "jboss_eap", "jboss_fuse", "jboss_ws")
"""Optional products that can be enabled or disabled for a scan."""
