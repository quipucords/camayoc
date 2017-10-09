# coding: utf-8
"""Models for use with the Quipucords API."""

import re
import uuid

from pprint import pformat

from camayoc.constants import MASKED_PASSWORD_OUTPUT


class HostCredential(object):
    """A class to aid in CRUD test cases for host credentials."""

    def __init__(
            self,
            name=None,
            username=None,
            password=None,
            ssh_keyfile=None,
            sudo_password=None,
            _id=None):
        """Host Credential objects encapsulate host credential data.

        Host credentials can be created by instantiating a HostCredential
        object. A unique name and username are provided by default.
        In order to create a valid host credential you must specify either a
        password or ssh_keyfile.

        Example::
            >>> from camayoc import api
            >>> from camayoc.qcs_models import HostCredential
            >>> client = api.QCS_Client()
            >>> host = HostCredential()
            >>> host.password = 'foo'
            >>> create_response = client.create_host_cred(host.payload())
            >>> host._id = create_response.json()['id']
        """
        self.name = str(uuid.uuid4()) if not name else name
        self.username = str(uuid.uuid4()) if not username else username
        self.password = password
        self.ssh_keyfile = ssh_keyfile
        self.sudo_password = sudo_password
        self._id = _id

    def fields(self):
        """Return a dictionary with all fields."""
        fields = self.payload()
        fields['id'] = self._id
        return fields

    def payload(self):
        """Return a dictionary for POST or PUT requests.

        Returns proper data for creating host credential with POST to
        /api/vi/credentials/hosts/ or updating host credential with PUT to
        /api/v1/credentials/hosts/{_id}

        """
        packet = {k: v for k, v in self.__dict__.items() if k != '_id'}
        return packet

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __eq__(self, other):
        """Return true if both objects are equal."""
        if isinstance(other, HostCredential):
            return self.__dict__ == other.__dict__

        diffs = 0
        password_matcher = re.compile(MASKED_PASSWORD_OUTPUT)
        for key, value in self.fields().items():
            if key == 'password':
                if not password_matcher.match(other.get(key)):
                    diffs += 1
            else:
                if not other.get(key) == value:
                    diffs += 1
        return diffs == 0

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other


class NetworkProfile(object):
    """A class to aid in CRUD test cases for network profiles."""

    def __init__(
            self,
            name=None,
            hosts=None,
            ssh_port=None,
            credential_ids=None,
            _id=None):
        """Objects of this type contain data associated with network profiles.

        Network profiles can be created on the quipucords server by
        instantiating a NetworkProfile object. A unique name and username are
        provided by default. In order to create a valid network profile,
        you must specify at least one existing host credential and one host.

        Example::
            >>> from camayoc import api
            >>> from camayoc.qcs_models import NetworkProfile
            >>> client = api.QCS_Client()

            >>> hostcred = HostCredential()
            >>> hostcred.password = 'foo'
            >>> create_response = client.create_host_cred(hostcred.payload())
            >>> hostcred._id = create_response.json()['id']

            >>> netprof = NetworkProfile(hosts=['0.0.0.0'],
                                         credential_ids=['host._id'])
            >>> client.create_net_prof(netprof.payload())
        """
        self.name = str(uuid.uuid4()) if not name else name
        self.hosts = hosts
        self.ssh_port = 22 if not name else name
        self.credentials = credential_ids
        self._id = _id

    def fields(self):
        """Return a dictionary with all fields."""
        fields = self.payload()
        fields['id'] = self._id
        return fields

    def payload(self):
        """Return a dictionary for POST or PUT requests.

        Returns proper data for creating host credential with POST to
        /api/vi/profiles/networks/ or updating host credential with PUT to
        /api/v1/profiles/networks/{_id}

        """
        packet = {k: v for k, v in self.__dict__.items() if k != '_id'}
        return packet

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __eq__(self, other):
        """Return true if both objects are equal."""
        if isinstance(other, NetworkProfile):
            return self.__dict__ == other.__dict__

        diffs = 0
        for key, value in self.fields().items():
            if key == 'credentials':
                other_creds = other.get('credentials')
                cred_ids = []
                for cred in other_creds:
                    cred_ids.append(cred.get('id'))
                if sorted(value) != sorted(cred_ids):
                    diffs += 1
            else:
                if not other.get(key) == value:
                    diffs += 1
        return diffs == 0

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other
