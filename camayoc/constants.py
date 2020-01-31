# coding=utf-8
"""Values usable by multiple test modules."""
from camayoc import utils

RHO_CONNECTION_FACTS = ("connection.host", "connection.port", "connection.uuid")
"""List of RHO's connection facts."""

RHO_JBOSS_FACTS = (
    "jboss.brms",
    "jboss.brms.summary",
    "jboss.eap.common-files",
    "jboss.eap.eap-home",
    "jboss.eap.init-files",
    "jboss.eap.jboss-user",
    "jboss.eap.locate-jboss-modules-jar",
    "jboss.eap.packages",
    "jboss.eap.processes",
    "jboss.eap.running-paths",
    "jboss.eap.summary",
    "jboss.fuse-on-karaf.karaf-home",
    "jboss.fuse.fuse-on-eap",
    "jboss.fuse.init-files",
    "jboss.fuse.summary",
)
"""List of RHO's jboss facts."""

RHO_JBOSS_ALL_FACTS = (
    "jboss.activemq-ver",
    "jboss.brms.drools-core-ver",
    "jboss.brms.kie-api-ver",
    "jboss.brms.kie-war-ver",
    "jboss.camel-ver",
    "jboss.cxf-ver",
    "jboss.eap.deploy-dates",
    "jboss.eap.find-jboss-modules-jar",
    "jboss.eap.installed-versions",
    "jboss.fuse-on-karaf.find-karaf-jar",
)
"""List of rho's additional jboss facts (for --facts all)."""

RHO_RHEL_FACTS = (
    "cpu.bogomips",
    "cpu.core_count",
    "cpu.count",
    "cpu.cpu_family",
    "cpu.hyperthreading",
    "cpu.model_name",
    "cpu.model_ver",
    "cpu.socket_count",
    "cpu.vendor_id",
    "date.anaconda_log",
    "date.date",
    "date.filesystem_create",
    "date.machine_id",
    "date.yum_history",
    "dmi.bios-vendor",
    "dmi.bios-version",
    "dmi.processor-family",
    "dmi.system-manufacturer",
    "etc-issue.etc-issue",
    "etc_release.name",
    "etc_release.release",
    "etc_release.version",
    "instnum.instnum",
    "redhat-packages.certs",
    "redhat-packages.gpg.is_redhat",
    "redhat-packages.gpg.last_built",
    "redhat-packages.gpg.last_installed",
    "redhat-packages.gpg.num_installed_packages",
    "redhat-packages.gpg.num_rh_packages",
    "redhat-release.name",
    "redhat-release.release",
    "redhat-release.version",
    "subman.consumed",
    "subman.cpu.core(s)_per_socket",
    "subman.cpu.cpu(s)",
    "subman.cpu.cpu_socket(s)",
    "subman.has_facts_file",
    "subman.virt.host_type",
    "subman.virt.is_guest",
    "subman.virt.uuid",
    "systemid.system_id",
    "systemid.username",
    "uname.all",
    "uname.hardware_platform",
    "uname.hostname",
    "uname.kernel",
    "uname.os",
    "uname.processor",
    "virt-what.type",
    "virt.num_guests",
    "virt.num_running_guests",
    "virt.type",
    "virt.virt",
)
"""List of RHO's RHEL facts."""

RHO_PRIVILEGED_FACTS = {
    "date.yum_history": {"denials": ["sudo: a password is required", "error"]},
    "date.anaconda_log": {"denials": ["error"]},
    "dmi.bios-vendor": {
        "denials": [
            "sudo: a password is required",
            "N/A (dmidecode not found)",
            "error",
        ]
    },
    "dmi.bios-version": {
        "denials": [
            "sudo: a password is required",
            "N/A (dmidecode not found)",
            "error",
        ]
    },
    "dmi.processor-family": {
        "denials": [
            "sudo: a password is required",
            "N/A (dmidecode not found)",
            "error",
        ]
    },
    "dmi.system-manufacturer": {
        "denials": [
            "sudo: a password is required",
            "N/A (dmidecode not found)",
            "error",
        ]
    },
    "jboss.brms.kie-war-ver": {"denials": ["(jboss.brms.kie-war-ver not found)"]},
    "jboss.brms.kie-api-ver": {"denials": ["(jboss.brms.kie-api-ver not found)"]},
    "jboss.brms.drools-core-ver": {
        "denials": ["(jboss.brms.drools-core-ver not found)"]
    },
    "jboss.fuse.cxf-ver": {"denials": ["(jboss.fuse.cxf-ver not found)"]},
    "jboss.fuse.camel-ver": {"denials": ["(jboss.fuse.camel-ver not found)"]},
    "jboss.fuse.activemq-ver": {"denials": ["(jboss.fuse.activemq-ver not found)"]},
    "jboss.eap.init-files": {
        "denials": [
            'Error: could not get output from "chkconfig"',
            "Error: all init system checks failed.",
        ]
    },
    "jboss.eap.locate-jboss-modules-jar": {
        "denials": [
            "Error code 127 running 'locate jboss-modules.jar': bash: locate: command not found ",  # noqa: E501
            "jboss-modules.jar not found",
        ]
    },
    "subman.consumed": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.cpu.core(s)_per_socket": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.cpu.cpu(s)": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.cpu.cpu_socket(s)": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.virt.host_type": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.virt.is_guest": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "subman.virt.uuid": {
        "denials": [
            "sudo: a password is required",
            "N/A (subscription-manager not found)",
            "error",
        ]
    },
    "virt.type": {
        "denials": [
            "sudo: a password is required",
            "error",
            "N/A (dmidecode not found)",
            "",
        ]
    },
    "virt.virt": {
        "denials": [
            "sudo: a password is required",
            "error",
            "N/A (dmidecode not found)",
            "",
        ]
    },
    "virt-what.type": {
        "denials": [
            "sudo: a password is required",
            "error",
            "N/A (virt-what not found)",
            "",
        ]
    },
    "virt.num_guests": {
        "denials": [
            "sudo: a password is required",
            "N/A (virsh not found)",
            "error",
            "",
        ]
    },
    "virt.num_running_guests": {
        "denials": [
            "sudo: a password is required",
            "N/A (virsh not found)",
            "error",
            "",
        ]
    },
}
"""Dictionary of facts that change based on privilege level.

When testing facts, we can differentiate between profiles that use credentials
with root/sudo privilege and those that do not. Those with root/sudo privilege
should obtain the fact as expected in the config file.

If the user is not marked as privileged, then instead of the value that the
root user should find, under privileged users may encounter any of the values
in the list of 'denials' and these will be considered valid scan values.
"""

RHO_DEFAULT_FACTS = RHO_CONNECTION_FACTS + RHO_JBOSS_FACTS + RHO_RHEL_FACTS
"""List of RHO's default facts."""

RHO_ALL_FACTS = RHO_DEFAULT_FACTS + RHO_JBOSS_ALL_FACTS
"""List of all rho facts."""

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

VAULT_PASSWORD_INPUT = "Please enter your rho vault password:"
"""Vault password input prompt."""

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
