"""Models for use with the Quipucords API."""

import re
from pprint import pformat
from typing import Optional
from urllib.parse import urljoin

from camayoc import api
from camayoc.constants import MASKED_AUTH_TOKEN_OUTPUT
from camayoc.constants import MASKED_PASSWORD_OUTPUT
from camayoc.constants import QPC_CREDENTIALS_PATH
from camayoc.constants import QPC_HOST_MANAGER_TYPES
from camayoc.constants import QPC_REPORTS_PATH
from camayoc.constants import QPC_SCAN_PATH
from camayoc.constants import QPC_SCANJOB_PATH
from camayoc.constants import QPC_SOURCE_PATH
from camayoc.exceptions import ScanJobWithoutReportException
from camayoc.types.settings import CredentialOptions
from camayoc.types.settings import ScanOptions
from camayoc.types.settings import SourceOptions
from camayoc.utils import server_container_ssh_key_content
from camayoc.utils import uuid4

OPTIONAL_PROD_KEY = "disabled_optional_products"
SENTINEL = object()


class QPCObjectBulkDeleteMixin(object):
    """Mixin that provides access to bulk_delete method.

    We can't put that in base model, because not all objects have
    bulk_delete endpoint; but we don't want to implement that for
    every object separately, because implementation is exactly the
    same for objects that do have this endpoint.
    """

    @api.try_reauthenticate
    def bulk_delete(self, ids, **kwargs):
        """Send POST request to the self.endpoint/bulk_delete/ of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.

        """
        path = urljoin(self.endpoint, "bulk_delete/")
        return self.client.post(path, payload={"ids": ids}, **kwargs)


class QPCObject(object):
    """A base class for other QPC models."""

    def __init__(self, client=None, _id=None):
        """Provide shared methods for QPC model objects."""
        # we want to allow for an empty string name
        self._id = _id
        self.client = client if client else api.Client()
        self.endpoint = ""

    def fields(self):
        """Return a dictionary with all fields.

        The fields are all data items that may be returned when a `GET` request
        is sent to the endpoint. It excludes items specific to camayoc such as
        the client and endpoint associated with objects of this type.
        """
        fields = self.payload()
        fields["id"] = self._id
        return fields

    def path(self):
        """Return the path to this object on the server.

        This concatenates the endpoint and the id of this object,
        to be used to read details about this object or to delete it.
        """
        return urljoin(self.endpoint, "{}/".format(self._id))

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {k: v for k, v in vars(self).items() if k not in ["_id", "client", "endpoint"]}

    def update_payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {
            k: v
            for k, v in vars(self).items()
            if k not in ["_id", "client", "endpoint", "cred_type", "source_type"]
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

    @api.try_reauthenticate
    def create(self, **kwargs):
        """Send POST request to the self.endpoint of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            ``request.request()`` method.

        Sends ``self.payload()`` as the data of the POST request, thereby
        creating an object on the server.

        Before returning the requests.models.Response to the caller, the
        ``_id`` of this object is set using the data from the response.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's ``self._id``.
        """
        response = self.client.post(self.endpoint, self.payload(), **kwargs)
        if response.status_code in range(200, 203):
            self._id = response.json().get("id")
            if response.json().get("port"):
                self.port = response.json().get("port")
        return response

    @api.try_reauthenticate
    def list(self, **kwargs):
        """Send GET request to read all objects of this type.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response
            contains a list of dictionaries with the data associated with each
            object of this type stored on the server.
        """
        return self.client.get(self.endpoint, **kwargs)

    @api.try_reauthenticate
    def read(self, **kwargs):
        """Send GET request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self._id`.
        """
        return self.client.get(self.path(), **kwargs)

    @api.try_reauthenticate
    def update(self, **kwargs):
        """Send PUT request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Sends `self.update_payload()` as the data of the PUT request, thereby
        updating the object on the server with the same `id` as this object
        with the fields contained in `self.update_payload()`.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self._id`.
        """
        return self.client.put(self.path(), self.update_payload(), **kwargs)

    @api.try_reauthenticate
    def delete(self, **kwargs):
        """Send DELETE request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.
        """
        return self.client.delete(self.path(), **kwargs)


class Credential(QPCObject, QPCObjectBulkDeleteMixin):
    """A class to aid in CRUD tests of Host Credentials on the QPC server.

    Host credentials can be created by instantiating a Credential
    object. A unique name and username are provided by default.
    In order to create a valid host credential you must specify either a
    password or ssh_key or auth_token.

    Example::
        >>> from camayoc import api
        >>> from camayoc.qpc_models import Credential
        >>> client = api.QPCClient()
        >>> cred = Credential(cred_type='network', password='foo')
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
        ssh_key=None,
        auth_token=None,
        cred_type=None,
        become_method=None,
        become_password=None,
        become_user=None,
        _id=None,
    ):
        """Create a host credential with given data.

        If no arguments are passed, then a api.Client will be initialized and a
        uuid4 generated for the name and username.
        """
        super().__init__(client=client, _id=_id)
        self.name = uuid4() if name is None else name
        self.endpoint = QPC_CREDENTIALS_PATH
        if auth_token is None and username is None:
            username = uuid4()
        self.username = username
        self.password = password
        self.ssh_key = ssh_key
        self.auth_token = auth_token
        self.cred_type = cred_type
        if become_method is not None:
            self.become_method = become_method
        if become_password is not None:
            self.become_password = become_password
        if become_user is not None:
            self.become_user = become_user

    @classmethod
    def from_definition(
        cls, definition: CredentialOptions, dependencies: Optional[list[int]] = None
    ):
        attrs_translation_map = {
            "sshkeyfile": "ssh_key",
            "type": "cred_type",
        }
        definition_data = {}
        for definition_key, definition_value in definition.model_dump().items():
            if definition_value is None:
                continue
            if new_definition_key := attrs_translation_map.get(definition_key):
                definition_key = new_definition_key
            if definition_key == "ssh_key":
                definition_value = server_container_ssh_key_content(definition_value)
            definition_data[definition_key] = definition_value
        return cls(**definition_data)

    def equivalent(self, other):
        """Return true if both objects are equal.

        :param other: This can be either another Credential or a dictionary
            or json object returned from the QPC server (or crafted by hand.)
            If `other` is a Credential instance, the two object's fields()
            will be compared. Otherwise, we expect the password to have been
            masked by the server.
        """
        if isinstance(other, Credential):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                "Objects of type Credential can only be compared to"
                "Credential objects or dictionaries."
            )

        password_matcher = re.compile(MASKED_PASSWORD_OUTPUT)
        token_matcher = re.compile(MASKED_AUTH_TOKEN_OUTPUT)
        local_items = self.fields()
        local_keys = local_items.keys()
        other_keys = other.keys()
        all_keys = set(local_keys).union(other_keys)
        for key in all_keys:
            if key not in [
                "password",
                "auth_token",
                "become_method",
                "become_user",
                "become_password",
                "created_at",
                "updated_at",
            ]:
                if not local_items.get(key) == other.get(key):
                    return False
            if "password" in key and local_items.get(key) is not None:
                if not password_matcher.match(other.get(key)):
                    return False
            if "auth_token" in key and local_items.get(key) is not None:
                if not token_matcher.match(other.get(key)):
                    return False
            if key == "become_method":
                if not other.get(key) == local_items.get(key, "sudo"):
                    return False
            if key == "become_user":
                if not other.get(key) == local_items.get(key, "root"):
                    return False
            if key in ("created_at", "updated_at"):
                if not other.get(key):
                    return False
        return True


class Source(QPCObject, QPCObjectBulkDeleteMixin):
    """A class to aid in CRUD test cases for sources.

    Sources can be created on the quipucords server by
    instantiating a Source object. A unique name and username are
    provided by default. In order to create a valid source,
    you must specify at least one existing host credential and one host.

    Example::
        >>> from camayoc.qpc_models import Source
        >>>
        >>> cred = Credential(cred_type='network',password='foo')
        >>> cred.create()
        >>> source = Source( source_type='network', hosts=['0.0.0.0'],
                                     credential_ids=[hostcred._id])
        >>> source.create()
        >>> actual_source = source.read().json()
        >>>
        >>> assert source.equivalent(actual_source)
    """

    def __init__(
        self,
        client=None,
        name=None,
        hosts=None,
        exclude_hosts=None,
        port=None,
        credential_ids=None,
        source_type=None,
        options=None,
        ssl_protocol=None,
        ssl_cert_verify=None,
        disable_ssl=None,
        use_paramiko=None,
        _id=None,
    ):
        """Initialize a Source object with given data.

        If no port is supplied, it will be set to 22 by default.
        A uuid4 name and api.Client are also supplied if none are provided.
        """
        super().__init__(client=client, _id=_id)
        self.name = uuid4() if name is None else name
        self.endpoint = QPC_SOURCE_PATH
        self.hosts = hosts
        if port is not None:
            self.port = port
        if options is not None:
            for opt in ("ssl_protocol", "ssl_cert_verify", "disable_ssl", "use_paramiko"):
                value = options.get(opt, SENTINEL)
                if value is SENTINEL:
                    continue
                setattr(self, opt, value)
        if ssl_protocol is not None:
            self.ssl_protocol = ssl_protocol
        if ssl_cert_verify is not None:
            self.ssl_cert_verify = ssl_cert_verify
        if disable_ssl is not None:
            self.disable_ssl = disable_ssl
        if use_paramiko is not None:
            self.use_paramiko = use_paramiko
        self.credentials = credential_ids
        self.source_type = source_type

    # Sources v2 does not provide bulk_delete endpoint, DISCOVERY-1006
    def bulk_delete(self, ids, **kwargs):
        old_endpoint = self.endpoint
        new_endpoint = old_endpoint.replace("v2/", "v1/")
        self.endpoint = new_endpoint
        retval = super().bulk_delete(ids, **kwargs)
        self.endpoint = old_endpoint
        return retval

    @classmethod
    def from_definition(cls, definition: SourceOptions, dependencies: Optional[list[int]] = None):
        attrs_translation_map = {
            "type": "source_type",
        }
        definition_data = {}
        for definition_key, definition_value in definition.model_dump().items():
            if definition_value is None:
                continue
            if new_definition_key := attrs_translation_map.get(definition_key):
                definition_key = new_definition_key
            if definition_key == "credentials":
                definition_key = "credential_ids"
                definition_value = dependencies
            definition_data[definition_key] = definition_value
        return cls(**definition_data)

    def equivalent(self, other):
        """Return true if both objects are equivalent.

        :param other: This can be either another Source or a dictionary
            or json object returned from the QPC server (or crafted by hand.)
            If `other` is a Source instance, the two object's fields()
            will be compared. Otherwise, we must extract the credential id's
            from the json returned by the server into a list, because that is
            all the data that we use to generate the source.
        """
        if isinstance(other, Source):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                "Objects of type Source can only be compared to Sources objects or dictionaries."
            )

        local_items = self.fields()
        local_keys = local_items.keys()
        other_keys = other.keys()
        all_keys = set(local_keys).union(other_keys)
        for key in all_keys:
            if key == "port":
                default_port = 22 if self.source_type == "network" else 443
                if int(other.get(key)) != int(local_items.get(key, default_port)):
                    return False
            if key == "options":
                if self.source_type in QPC_HOST_MANAGER_TYPES:
                    if hasattr(self, "options"):
                        ssl_verify = self.options.get("ssl_cert_verify", True)
                    else:
                        ssl_verify = True
                    if other.get(key, {}).get("ssl_cert_verify") != ssl_verify:
                        return False

            if key == "credentials":
                other_creds = other.get("credentials")
                cred_ids = []
                # the server returns a list of dictionaries
                # one for each credential associated with the Source
                # we extract from this all the id's and then compare it with
                # the list of id's we used to create the source
                for cred in other_creds:
                    cred_ids.append(cred.get("id"))
                if sorted(local_items.get(key)) != sorted(cred_ids):
                    return False

            if key not in ["port", "credentials", "options"]:
                if not other.get(key) == local_items.get(key):
                    return False
        return True


class Scan(QPCObject, QPCObjectBulkDeleteMixin):
    """A class to aid in CRUD test cases for scan jobs.

    Scans are named objects on the server that can then be used to generate any
    number of scan jobs. The Scan object determines the sources, max
    concurrency settings, and (not yet implemented) the products to search
    for/not search for.

    The id of an existing Source is necessary to create a Scan.
    An existing Scan is necessary to create a ScanJob.

    Example::
        >>> cred = Credential(cred_type='network', password='foo')
        >>> cred.create()
        >>> src = Source(
                            source_type='network',
                            hosts=['0.0.0.0'],
                            credential_ids=[cred._id]
                            )
        >>> src.create()
        >>> scan = Scan(source_ids=[src._id])
        >>> scan.create()
        >>> scanjob = ScanJob(scan._id)
        >>> scanjob.create()
        >>> assert scanjob.status() == 'running'
    """

    def __init__(
        self,
        client=None,
        source_ids=None,
        max_concurrency=50,
        disabled_optional_products=None,
        enabled_extended_product_search=None,
        scan_type="inspect",
        name=None,
        _id=None,
    ):
        """Iniitalize a Scan object with given data.

        If no value for max_concurrency is given, it will be set to 50, and if
        no value for scan_type is given, the default type is host (for which
        facts are collected). The other valid option for scan_type is
        'discovery' in which no facts are collected, the server simply sees how
        many hosts in the source it can make contact and log into.
        """
        super().__init__(client=client, _id=_id)

        self.sources = source_ids
        self.endpoint = QPC_SCAN_PATH
        self.name = uuid4() if name is None else name

        # only valid scan type is 'inspect'
        self.scan_type = scan_type
        self.options = {"max_concurrency": max_concurrency}
        if disabled_optional_products:
            self.options["disabled_optional_products"] = disabled_optional_products
        if enabled_extended_product_search:
            self.options["enabled_extended_product_search"] = enabled_extended_product_search

    @classmethod
    def from_definition(cls, definition: ScanOptions, dependencies: Optional[list[int]] = None):
        definition_data = {}
        for definition_key, definition_value in definition.model_dump().items():
            if definition_value is None:
                continue
            if definition_key == "sources":
                definition_key = "source_ids"
                definition_value = dependencies
            definition_data[definition_key] = definition_value
        definition_data.pop("expected_data", None)
        return cls(**definition_data)

    @api.try_reauthenticate
    def delete(self, **kwargs):
        """Send DELETE request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.
        """
        return self.client.delete(self.path(), **kwargs)

    @api.try_reauthenticate
    def joblist(self, **kwargs):
        """Ask the server to list the ScanJobs associated with this scan.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.
        """
        path = urljoin(self.path(), "jobs/")
        return self.client.get(path, **kwargs)

    def equivalent(self, other):
        """Return true if both objects are equivalent.

        :param other: This can be either another Scan or a dictionary
            or json object returned from the QPC server (or crafted by hand.)
            If `other` is a Scan instance, the two object's fields()
            will be compared.

            For a dictionary, we expect the format returned by the server with
            self.read(), in which case we must extract the source id from a
            dictionary.
        """
        if isinstance(other, Scan):
            return self.fields() == other.fields()

        if not isinstance(other, dict):
            raise TypeError(
                "Objects of type Scan can only be compared to Scan objects or dictionaries."
            )

        local_items = self.fields()
        local_keys = local_items.keys()
        other_keys = other.keys()
        all_keys = set(local_keys).union(other_keys)
        for key in all_keys:
            if key == "status":
                continue
            if key == "sources":
                other_sources = [src["id"] for src in other[key]]
                if sorted(local_items[key]) != sorted(other_sources):
                    return False
            if key not in ["status", "sources", "options"]:
                if not other[key] == local_items[key]:
                    return False
        return True


class ScanJob(QPCObject):
    """A class to aid in the creation and control of Scan Jobs in tests."""

    def __init__(self, client=None, scan_id=None, _id=None):
        """Initialize a ScanJob object for a given scan."""
        super().__init__(client=client, _id=_id)

        self.scan_id = scan_id
        self.endpoint = QPC_SCANJOB_PATH

    @api.try_reauthenticate
    def create(self, **kwargs):
        """Send POST request to the scan's job endpoint.

        Overrides parent class's create method because ScanJobs act
        differently than everything else.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            ``request.request()`` method.

        Before returning the requests.models.Response to the caller, the
        ``_id`` of this object is set using the data from the response.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's ``self._id``.
        """
        path = urljoin(QPC_SCAN_PATH, "{}/jobs/".format(self.scan_id))
        response = self.client.post(path, payload=self.payload(), **kwargs)
        if response.status_code in range(200, 203):
            self._id = response.json().get("id")
        return response

    @api.try_reauthenticate
    def list(self, **kwargs):
        """Send GET request to read all scanjobs associated with the same scan.

        Overrides parent class's create method because ScanJobs act
        differently than everything else.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response
            contains a list of dictionaries with the data associated with each
            object of this type stored on the server.
        """
        path = urljoin(QPC_SCAN_PATH, "{}/jobs/".format(self.scan_id))
        return self.client.get(path, **kwargs)

    @api.try_reauthenticate
    def cancel(self, **kwargs):
        """Send PUT request to self.endpoint/{id}/cancel/ to cancel a scan.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), "cancel/")
        return self.client.put(path, {}, **kwargs)

    @api.try_reauthenticate
    def connection_results(self, **kwargs):
        """Send a GET self.endpoint/{id}/connection/ to read scan details.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), "connection/")
        return self.client.get(path, **kwargs)

    @api.try_reauthenticate
    def inspection_results(self, **kwargs):
        """Send a GET self.endpoint/{id}/inspection/ to read scan details.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.path(), "inspection/")
        return self.client.get(path, **kwargs)

    def status(self):
        """Check on the status of the scan.

        Note: only scans that have been posted to the server have a status.
        If you call this method on a scan that does not exist on the server,
        you will get an HTTPError.
        """
        return self.read().json().get("status")

    def equivalent(self, other):
        """Alert the user that this method is not implemented.

        :raises: NotImplementedError
        """
        raise NotImplementedError("ScanJobs do not have an equivalent() method.")


class Report(QPCObject):
    """A class to aid in the creation and control of Reports.

    Reports are generated by the fact collection carried out through
    scan jobs. There are two types of reports that can be generated,
    a detail report and a deployments report.

    The ids of existing Scan Jobs are necessary to create a report from
    merging.

    Example::
        >>> cred = Credential(cred_type='network', password='foo')
        >>> cred.create()
        >>> src = Source(
                            source_type='network',
                            hosts=['0.0.0.0'],
                            credential_ids=[cred._id]
                            )
        >>> src.create()
        >>> scan = Scan(source_ids=[src._id])
        >>> scan.create()
        >>> scanjob = ScanJob(scan._id)
        >>> scanjob2 = ScanJob(scan._id)
        >>> scanjob.create()
        >>> scanjob2.create()
        >>> report = Report()
        >>> report.deployments()
        >>> report.details()
    """

    def __init__(self, client=None, _id=None):
        """Initialize a Report Object."""
        super().__init__(client=client, _id=_id)

        self.endpoint = QPC_REPORTS_PATH
        self._id = _id

    @api.try_reauthenticate
    def retrieve_from_scan_job(self, scan_job_id, **kwargs):
        """Send GET request to /jobs/<scan_job_id>/ to get a scanjob.

        :param ``scan_job_id``: A scan job identifier
        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(QPC_SCANJOB_PATH, str(scan_job_id), "/")
        response = self.client.get(path, **kwargs)
        if response.status_code in range(200, 203):
            self._id = response.json().get("report_id")
        if not self._id:
            response_data = response.json()
            msg = (
                "Scan job does not have report_id."
                " scan_job_id={} scan.name={} status={} status_message:\n{}"
            )
            raise ScanJobWithoutReportException(
                msg.format(
                    response_data.get("id"),
                    response_data.get("scan", {}).get("name"),
                    response_data.get("status"),
                    response_data.get("status_message"),
                )
            )
        return response

    @api.try_reauthenticate
    def details(self, **kwargs):
        """Send GET request to self.endpoint/{id}/details/ to view the report details.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.endpoint, "{}/details/".format(self._id))
        response = self.client.get(path, **kwargs)
        return response

    @api.try_reauthenticate
    def deployments(self, **kwargs):
        """Send GET request to self.endpoint/{id}/deployments/ to view deployments.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.endpoint, "{}/deployments/".format(self._id))
        response = self.client.get(path, **kwargs)
        return response

    @api.try_reauthenticate
    def aggregate(self, **kwargs):
        """Send GET request to self.endpoint/{id}/aggregate/ to view the aggregate report.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        path = urljoin(self.endpoint, "{}/aggregate/".format(self._id))
        response = self.client.get(path, **kwargs)
        return response

    @api.try_reauthenticate
    def reports_gzip(self, **kwargs):
        """Send GET request to self.endpoint/{id}/ to obtain report in gzip format.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.
        """
        extra_headers = {"Accept": "application/gzip"}
        path = urljoin(self.endpoint, "{}/".format(self._id))
        response = self.client.get(path, headers=extra_headers, **kwargs)
        return response
