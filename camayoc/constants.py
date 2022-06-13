# coding=utf-8
"""Values usable by multiple test modules."""
from camayoc import utils

MASKED_PASSWORD_OUTPUT = r"\*{8}"
"""Regex that matches password on outputs."""

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

QPC_SOURCE_TYPES = ("vcenter", "network", "satellite")
"""Types of sources that the quipucords server supports."""

QPC_SCAN_TYPES = ("inspect", "connect")
"""Types of scans that the quipucords server supports."""

QPC_HOST_MANAGER_TYPES = ("vcenter", "satellite")
"""Types of host managers that the quipucords server supports."""

QPC_BECOME_METHODS = ("doas", "dzdo", "ksu", "pbrun", "pfexec", "runas", "su", "sudo")
"""Supported become methods for quipucords server."""

QPC_OPTIONAL_PRODUCTS = ("jboss_brms", "jboss_eap", "jboss_fuse", "jboss_ws")
"""Optional products that can be enabled or disabled for a scan."""

QPC_FUSE_RAW_FACTS = (
    "karaf_locate_karaf_jar",
    "karaf_homes",
    "karaf_home_bin_fuse",
    "karaf_home_system_org_jboss",
    "fuse_activemq_version",
    "karaf_running_processes",
    "jboss_fuse_systemctl_unit_files",
    "jboss_fuse_chkconfig",
    "fuse_camel_version",
    "fuse_cxf_version",
)
"""List of facts collected by JBoss FUSE role."""

QPC_BRMS_RAW_FACTS = (
    "internal_jboss_brms_business_central_candidates",
    "jboss_brms_business_central_candidates",
    "jboss_brms_kie_server_candidates",
    "business_central_candidates_eap",
    "kie_server_candidates_eap",
    "jboss_brms_locate_kie_api",
    "internal_jboss_brms_locate_kie_api",
    "jboss_brms_kie_in_business_central",
    "jboss_brms_manifest_mf",
    "business_central_candidates",
)
"""List of facts collected by JBoss BRMS role."""

QPC_EAP_RAW_FACTS = (
    "jboss_eap_running_paths",
    "jboss_eap_locate_jboss_modules_jar",
    "eap_home_candidates",
    "eap_home_ls",
    "eap_home_version_txt",
    "eap_home_readme_txt",
    "eap_home_jboss_modules_manifest",
    "eap_home_jboss_modules_version",
    "eap_home_bin",
    "eap_home_layers",
    "eap_home_layers_conf",
    "jboss_eap_common_files",
    "jboss_eap_processes",
    "jboss_eap_packages",
)
"""List of facts collected by JBoss EAP role."""

QPC_FUSE_EXTENDED_FACTS = (
    "jboss_activemq_ver",
    "jboss_camel_ver",
    "jboss_cxf_ver",
    "karaf_find_karaf_jar",
)
"""List of facts collected by JBoss FUSE Extended tasks."""

QPC_BRMS_EXTENDED_FACTS = (
    "jboss_brms_kie_api_ver",
    "jboss_brms_drools_core_ver",
    "jboss_brms_kie_war_ver",
)
"""List of facts collected by JBoss BRMS Extended tasks."""

QPC_EAP_EXTENDED_FACTS = (
    "jboss_eap_find_jboss_modules_jar",
    "jboss_eap_jar_ver",
    "jboss_eap_run_jar_ver",
)
"""List of facts collected by JBoss EAP Extended tasks."""
