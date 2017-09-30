# coding: utf-8
"""Models for use with the Quipucords API."""

import uuid
from pprint import pformat


class HostCredential(object):
    """A host credential for the QCS server."""

    def __init__(
            self,
            name=None,
            username=None,
            password=None,
            ssh_keyfile=None,
            sudo_password=None,
            host_id=None):
        """Host Credential objects encapsulate host credential data.

        Host credentials can be created by instantating a HostCredential
        object. A unique name and username are provided by default.
        In order to create a valid host credential you must specify either a
        password or ssh_keyfile.

        Example::
            >>> from camayoc import api
            >>> from camayoc.qcs_models import HostCredential
            >>> client = api.QCS_Client()
            >>> host = HostCredential()
            >>> host.password = 'foo'
            >>> client.create_host_cred(host.payload())
        """
        self.name = str(uuid.uuid4()) if not name else name
        self.username = str(uuid.uuid4()) if not username else username
        self.password = password
        self.ssh_keyfile = ssh_keyfile
        self.sudo_password = sudo_password
        self.host_id = host_id

    def fields(self):
        """Return a dictionary with all fields."""
        fields = self.payload()
        fields['id'] = self.host_id
        return fields

    def payload(self):
        """Return a dictionary for POST or PUT requests.

        Returns proper package for creating host credential with POST to
        /api/vi/credentials/hosts/ or updating host credential with PUT to
        /api/v1/credentials/hosts/{host_id}

        """
        packet = {k: v for k, v in self.__dict__.items() if k != 'host_id'}
        return packet

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __eq__(self, other):
        """Return true if both objects are equal."""
        if not isinstance(other, HostCredential):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other
