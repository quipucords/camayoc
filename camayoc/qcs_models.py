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
    QCS_SCAN_PATH,
)


class QCSObject(object):
    """A base class for other QCS models."""

    def __init__(
            self,
            client=None,
            _id=None):
        """Provide shared methods for QCS model objects."""
        # we want to allow for an empty string name
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
        self._id = response.json().get('id')
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
        super().__init__(client=client, _id=_id)
        self.name = str(uuid.uuid4()) if name is None else name
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

        password_matcher = re.compile(MASKED_PASSWORD_OUTPUT)
        for key, value in self.fields().items():
            if key == 'password' and other.get(key) is not None:
                if not password_matcher.match(other.get(key)):
                    return False
            else:
                if not other.get(key) == value:
                    return False
        return True


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
        super().__init__(client=client, _id=_id)
        self.name = str(uuid.uuid4()) if name is None else name
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
                    return False
            else:
                if not other.get(key) == value:
                    return False
        return True


class Scan(QCSObject):
    """A class to aid in CRUD test cases for scan jobs.

    Scan jobs can be created on the quipucords server by instantiating a Scan
    object and then calling its create() method.

    The id of an existing NetworkProfile is necessary to create a scan
    job.

    Example::
        >>> hostcred = HostCredential(password='foo')
        >>> hostcred.create()
        >>> netprof = NetworkProfile(hosts=['0.0.0.0'],
                                     credential_ids=[hostcred._id])
        >>> netprof.create()
        >>> scan = Scan(profile_id=netprof._id)
        >>> scan.create()
        >>> scan.pause()
        >>> assert scan.status() == 'paused'
    """

    def __init__(
            self,
            client=None,
            source_id=None,
            max_concurrency=50,
            scan_type='host',
            _id=None):
        """Iniitalize a Scan object with given data.

        If no value for max_concurrency is given, it will be set to 50, and if
        no value for scan_type is given, the default type is host (for which
        facts are collected). The other valid option for scan_type is
        'discovery' in which no facts are collected, the server simply sees how
        many hosts in the profile it can make contact and log into.
        """
        super().__init__(client=client, _id=_id)

        self.source = source_id
        self.endpoint = QCS_SCAN_PATH

        # valid scan types are 'host' and 'discovery'
        self.scan_type = scan_type
        self.max_concurrency = max_concurrency

    def delete(self):
        """No delete method is implemented for scan objects.

        Raise an exception to alert the user of this instead of doing anything.
        """
        raise NotImplementedError(
            'the DELETE method is not allowed for the scan endpoint, '
            'so this method is not implemented for Scan objects.'
        )

    def pause(self, **kwargs):
        """Send PUT request to self.endpoint/{id}/pause/ to pause a scan.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), 'pause/')
        return self.client.put(path, {}, **kwargs)

    def cancel(self, **kwargs):
        """Send PUT request to self.endpoint/{id}/cancel/ to cancel a scan.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), 'cancel/')
        return self.client.put(path, {}, **kwargs)

    def restart(self, **kwargs):
        """Send PUT request to self.endpoint/{id}/restart/ to restart a scan.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), 'restart/')
        return self.client.put(path, {}, **kwargs)

    def status(self):
        """Check on the status of the scan.

        Note: only scans that have been posted to the server have a status.
        If you call this method on a scan that does not exist on the server,
        you will get an HTTPError.
        """
        return self.read().json().get('status')

    def equivalent(self, other):
        """Return true if both objects are equivalent.

        :param other: This can be either another Scan or a dictionary
            or json object returned from the QCS server (or crafted by hand.)
            If `other` is a Scan instance, the two object's fields()
            will be compared.

            For a dictionary, we expect the format returned by the server with
            self.read(), in which case we must extract the profile id from a
            dictionary.
        """
        if isinstance(other, Scan):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                'Objects of type Scan can only be compared to'
                'Scan objects or dictionaries.'
            )

        for key, value in self.fields().items():
            if key == 'profile':
                if value != other.get(key).get('id'):
                    return False
            else:
                if not other.get(key) == value:
                    return False
        return True
