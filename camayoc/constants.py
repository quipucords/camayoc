# coding=utf-8
"""Values usable by multiple test modules."""
from camayoc import utils

RHO_CONNECTION_FACTS = (
    'connection.host',
    'connection.port',
    'connection.uuid',
)
"""List of RHO's connection facts."""

RHO_JBOSS_FACTS = (
    'jboss.eap.common-files',
    'jboss.eap.jboss-user',
    'jboss.eap.packages',
    'jboss.eap.processes',
    'jboss.eap.running-paths',
)
"""List of RHO's jboss facts."""

RHO_JBOSS_ALL_FACTS = (
    'jboss.brms.drools-core-ver',
    'jboss.brms.kie-api-ver',
    'jboss.brms.kie-war-ver',
    'jboss.eap.deploy-dates',
    'jboss.eap.installed-versions',
    'jboss.fuse.activemq-ver',
    'jboss.fuse.camel-ver',
    'jboss.fuse.cxf-ver',
)
"""List of rho's additional jboss facts (for --facts all)."""

RHO_RHEL_FACTS = (
    'cpu.bogomips',
    'cpu.core_count',
    'cpu.count',
    'cpu.cpu_family',
    'cpu.hyperthreading',
    'cpu.model_name',
    'cpu.model_ver',
    'cpu.socket_count',
    'cpu.vendor_id',
    'date.anaconda_log',
    'date.date',
    'date.filesystem_create',
    'date.machine_id',
    'date.yum_history',
    'dmi.bios-vendor',
    'dmi.bios-version',
    'dmi.processor-family',
    'dmi.system-manufacturer',
    'etc-issue.etc-issue',
    'etc_release.name',
    'etc_release.release',
    'etc_release.version',
    'instnum.instnum',
    'redhat-packages.certs',
    'redhat-packages.gpg.is_redhat',
    'redhat-packages.gpg.last_built',
    'redhat-packages.gpg.last_installed',
    'redhat-packages.gpg.num_installed_packages',
    'redhat-packages.gpg.num_rh_packages',
    'redhat-packages.is_redhat',
    'redhat-packages.last_built',
    'redhat-packages.last_installed',
    'redhat-packages.num_installed_packages',
    'redhat-packages.num_rh_packages',
    'redhat-release.name',
    'redhat-release.release',
    'redhat-release.version',
    'subman.consumed',
    'subman.cpu.core(s)_per_socket',
    'subman.cpu.cpu(s)',
    'subman.cpu.cpu_socket(s)',
    'subman.has_facts_file',
    'subman.virt.host_type',
    'subman.virt.is_guest',
    'subman.virt.uuid',
    'systemid.system_id',
    'systemid.username',
    'uname.all',
    'uname.hardware_platform',
    'uname.hostname',
    'uname.kernel',
    'uname.os',
    'uname.processor',
    'virt-what.type',
    'virt.num_guests',
    'virt.num_running_guests',
    'virt.type',
    'virt.virt',
)
"""List of RHO's RHEL facts."""

RHO_PRIVILEGED_FACTS = {
    'date.yum_history': {
        'denials': [
            'sudo: a password is required',
            'error'
        ]
    },
    'date.anaconda_log': {
        'denials': [
            'error',
        ]
    },
    'dmi.bios-vendor': {
        'denials': [
            'sudo: a password is required',
            'N/A (dmidecode not found)',
            'error',
        ]
    },
    'dmi.bios-version': {
        'denials': [
            'sudo: a password is required',
            'N/A (dmidecode not found)',
            'error',
        ]
    },
    'dmi.processor-family': {
        'denials': [
            'sudo: a password is required',
            'N/A (dmidecode not found)',
            'error',
        ]
    },
    'dmi.system-manufacturer': {
        'denials': [
            'sudo: a password is required',
            'N/A (dmidecode not found)',
            'error',
        ]
    },
    'jboss.brms.kie-war-ver': {
        'denials': [
            '(jboss.brms.kie-war-ver not found)',
        ]
    },
    'jboss.brms.kie-api-ver': {
        'denials': [
            '(jboss.brms.kie-api-ver not found)',
        ]
    },
    'jboss.brms.drools-core-ver': {
        'denials': [
            '(jboss.brms.drools-core-ver not found)',
        ]
    },
    'jboss.fuse.cxf-ver': {
        'denials': [
            '(jboss.fuse.cxf-ver not found)',
        ]
    },
    'jboss.fuse.camel-ver': {
        'denials': [
            '(jboss.fuse.camel-ver not found)',
        ]
    },
    'jboss.fuse.activemq-ver': {
        'denials': [
            '(jboss.fuse.activemq-ver not found)',
        ]
    },
    'subman.consumed': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.cpu.core(s)_per_socket': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.cpu.cpu(s)': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.cpu.cpu_socket(s)': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.virt.host_type': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.virt.is_guest': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'subman.virt.uuid': {
        'denials': [
            'sudo: a password is required',
            'N/A (subscription-manager not found)',
            'error',
        ]
    },
    'virt.type': {
        'denials': [
            'sudo: a password is required',
            'error',
            'N/A (dmidecode not found)',
            '',
        ]
    },
    'virt.virt': {
        'denials': [
            'sudo: a password is required',
            'error',
            'N/A (dmidecode not found)',
            '',
        ]
    },
    'virt-what.type': {
        'denials': [
            'sudo: a password is required',
            'error',
            'N/A (virt-what not found)',
            '',
        ]
    },
    'virt.num_guests': {
        'denials': [
            'sudo: a password is required',
            'N/A (virsh not found)',
            'error',
            '',
        ]
    },
    'virt.num_running_guests': {
        'denials': [
            'sudo: a password is required',
            'N/A (virsh not found)',
            'error',
            '',
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

MASKED_PASSWORD_OUTPUT = '\*{8}'
"""Regex that matches password on outputs."""

CONNECTION_PASSWORD_INPUT = 'Provide connection password.\r\nPassword:'
"""Connection password input prompt."""

SUDO_PASSWORD_INPUT = 'Provide password for sudo.\r\nPassword:'
"""Sudo password input prompt."""

VAULT_PASSWORD = utils.uuid4()
"""Vault password will be unique across Python sessions."""

VAULT_PASSWORD_INPUT = 'Please enter your rho vault password:'
"""Vault password input prompt."""

VCENTER_DATA_CENTER = 0
"""The index of the VCenter data center in the MOB"""

VCENTER_CLUSTER = 1
"""The index of the cluster in the data center in the VCenter MOB"""

VCENTER_HOST = 0
"""The index of the host in the cluster in the VCenter MOB"""

QCS_API_VERSION = 'api/v1/'
"""The root path to access the QCS server API."""

QCS_CREDENTIALS_PATH = 'credentials/hosts/'
"""The path to the credentials endpoint for CRUD tasks."""

QCS_PROFILES_PATH = 'profiles/networks/'
"""The path to the profiles endpoint for CRUD tasks."""
