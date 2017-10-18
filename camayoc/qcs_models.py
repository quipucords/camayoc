# coding: utf-8
"""Models for use with the Quipucords API."""

import re
import uuid

from pprint import pformat
from urllib.parse import urljoin

from camayoc import api
from camayoc.constants import MASKED_PASSWORD_OUTPUT
from camayoc.constants import (
    QCS_CREDENTIALS_PATH,
    QCS_PROFILES_PATH,
)


class QCSObject(object):
    """A base class for other QCS models."""

    def __init__(
            self,
            client=None,
            name=None,
            _id=None):
        """Provide shared methods for QCS model objects."""
        # we want to allow for an empty string name
        self.name = str(uuid.uuid4()) if name is None else name
        self._id = _id
        self.client = client if client else api.Client()
        self.endpoint = ''

    def fields(self):
        """Return a dictionary with all fields.

        The fields are all data items that may be returned when a `GET` request
        is sent to the endpoint. It excludes items specific to camayoc such as
        the client and endpoint associated with objects of this type.
        """
        fields = self.payload()
        fields['id'] = self._id
        return fields

    def path(self):
        """Return the path to this object on the server.

        This concatenates the endpoint and the id of this object,
        to be used to read details about this object or to delete it.
        """
        return urljoin(self.endpoint, '{}/'.format(self._id))

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {
            k: v for k, v in vars(self).items()
            if k not in ['_id', 'client', 'endpoint']
        }

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other

    def create(self, **kwargs):
        """Send POST request to the self.endpoint of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            ``request.request()`` method.

        Sends ``self.payload()`` as the data of the POST request, thereby
        creating an object on the server.

        Before returning the requests.models.Response to the caller, the
        ``_id`` of this object is set using the data from the response.

        Returns a requests.models.Response. The json of this response contains
        the data associated with this object's ``self._id``.
        """
        response = self.client.post(self.endpoint, self.payload(), **kwargs)
        self._id = response.json()['id']
        return response

    def list(self, **kwargs):
        """Send GET request to read all objects of this type.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Returns a requests.models.Response. The json of this response
        contains a list of dictionaries with the data associated with each
        object of this type stored on the server.
        """
        return self.client.get(self.endpoint, **kwargs)

    def read(self, **kwargs):
        """Send GET request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Returns a requests.models.Response. The json of this response contains
        the data associated with this object's `self._id`.
        """
        return self.client.get(self.path(), **kwargs)

    def update(self, **kwargs):
        """Send PUT request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Sends `self.payload()` as the data of the PUT request, thereby updating
        the object on the server with the same `id` as this object with the
        fields contained in `self.payload()`.

        Returns a requests.models.Response. The json of this response contains
        the data associated with this object's `self._id`.
        """
        return self.client.put(self.path(), self.payload(), **kwargs)

    def delete(self, **kwargs):
        """Send DELETE request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Returns a requests.models.Response. A successful delete has the return
        code `204`.
        """
        return self.client.delete(self.path(), **kwargs)


class HostCredential(QCSObject):
    """A class to aid in CRUD tests of Host Credentials on the QCS server.

    Host credentials can be created by instantiating a HostCredential
    object. A unique name and username are provided by default.
    In order to create a valid host credential you must specify either a
    password or ssh_keyfile.

    Example::
        >>> from camayoc import api
        >>> from camayoc.qcs_models import HostCredential
        >>> client = api.QCSClient()
        >>> cred = HostCredential(password='foo')
        >>> # The create method automatically sets the credential's `_id`
        >>> cred.create()
        >>> actual_cred = cred.read().json()
        >>> assert actual_cred.equivalent(cred)
    """

    def __init__(
            self,
            client=None,
            name=None,
            username=None,
            password=None,
            ssh_keyfile=None,
            sudo_password=None,
            _id=None):
        """Create a host credential with given data.

        If no arguments are passed, then a api.Client will be initialized and a
        uuid4 generated for the name and username.

        For a HostCredential to be successfully created on the QCS server,
        a password XOR a ssh_keyfile must be provided.
        """
        super().__init__(client=client, name=name, _id=_id)
        self.endpoint = QCS_CREDENTIALS_PATH
        self.username = str(uuid.uuid4()) if username is None else username
        self.password = password
        self.ssh_keyfile = ssh_keyfile
        self.sudo_password = sudo_password

    def equivalent(self, other):
        """Return true if both objects are equal.

        :param other: This can be either another HostCredential or a dictionary
            or json object returned from the QCS server (or crafted by hand.)
            If `other` is a HostCredential instance, the two object's fields()
            will be compared. Otherwise, we expect the password to have been
            masked by the server.
        """
        if isinstance(other, HostCredential):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                'Objects of type HostCredential can only be compared to'
                'HostCredential objects or dictionaries.'
            )

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


class NetworkProfile(QCSObject):
    """A class to aid in CRUD test cases for network profiles.

    Network profiles can be created on the quipucords server by
    instantiating a NetworkProfile object. A unique name and username are
    provided by default. In order to create a valid network profile,
    you must specify at least one existing host credential and one host.

    Example::
        >>> from camayoc.qcs_models import NetworkProfile
        >>>
        >>> hostcred = HostCredential(password='foo')
        >>> hostcred.create()
        >>> netprof = NetworkProfile(hosts=['0.0.0.0'],
                                     credential_ids=[hostcred._id])
        >>> netprof.create()
        >>> actual_prof = netprof.read().json()
        >>>
        >>>
        >>> assert actual_prof.equivalent(netprof)
    """

    def __init__(
            self,
            client=None,
            name=None,
            hosts=None,
            ssh_port=22,
            credential_ids=None,
            _id=None):
        """Iniitalize a NetworkProfile object with given data.

        If no ssh_port is supplied, it will be set to 22 by default.
        A uuid4 name and api.Client are also supplied if none are provided.
        """
        super().__init__(client=client, name=name, _id=_id)
        self.endpoint = QCS_PROFILES_PATH
        self.hosts = hosts
        self.ssh_port = ssh_port
        self.credentials = credential_ids

    def equivalent(self, other):
        """Return true if both objects are equivalent.

        :param other: This can be either another NetworkProfile or a dictionary
            or json object returned from the QCS server (or crafted by hand.)
            If `other` is a NetworkProfile instance, the two object's fields()
            will be compared. Otherwise, we must extract the credential id's
            from the json returned by the server into a list, because that is
            all the data that we use to generate the network profile.
        """
        if isinstance(other, NetworkProfile):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                'Objects of type NetworkProfile can only be compared to'
                'NetworkProfiles objects or dictionaries.'
            )

        diffs = 0
        for key, value in self.fields().items():
            if key == 'credentials':
                other_creds = other.get('credentials')
                cred_ids = []
                # the server returns a list of dictionaries
                # one for each credential associated with the NetworkProfile
                # we extract from this all the id's and then compare it with
                # the list of id's we used to create the Network Profile
                for cred in other_creds:
                    cred_ids.append(cred.get('id'))
                if sorted(value) != sorted(cred_ids):
                    diffs += 1
            else:
                if not other.get(key) == value:
                    diffs += 1
        return diffs == 0
