# coding=utf-8
"""Client for working with QCS's API.

This module provides a flexible API client for talking with the quipucords
server, allowing the user to customize how return codes are handled depending
on the context.

"""

import requests

from urllib.parse import urljoin

from camayoc import config
from camayoc import exceptions


def echo_handler(server_config, response):  # pylint:disable=unused-argument
    """Immediately return ``response``."""
    return response


def code_handler(server_config, response):  # pylint:disable=unused-argument
    """Check the response status code, and return the response.

    :raises: ``requests.exceptions.HTTPError`` if the response status code is
        in the 4XX or 5XX range.
    """
    response.raise_for_status()
    return response


def json_handler(server_config, response):
    """Like ``code_handler``, but also return a JSON-decoded response body.

    Do what :func:`camayoc.api.code_handler` does. In addition, decode the
    response body as JSON and return the result.
    """
    response.raise_for_status()
    return response.json()


class Client(object):
    """A client for interacting with the quipucords API.

    This class is a wrapper around the ``requests.api`` module provided by
    `Requests`_. Each of the functions from that module are exposed as methods
    here, and each of the arguments accepted by Requests' functions are also
    accepted by these methods. The difference between this class and the
    `Requests`_ functions lies in its configurable request and response
    handling mechanisms.

    All requests made via this client use the base URL of the qcs server
    provided in your ``$XDG_CONFIG_HOME/camayoc/config.yaml``.

    You can override this base url by assigning a new value to the url
    field.

    Example::
        >>> from camayoc import api
        >>> client = api.Client()
        >>> # I can now make requests to the QCS server
        >>> # using relative paths, because the base url is
        >>> # was set using my config file.
        >>>
        >>> client.get('/credentials/hosts/')
        >>>
        >>> # now if I want to do something else,
        >>> # I can change the base url
        >>> client.url = 'www.whatever.com'

    .. _Requests: http://docs.python-requests.org/en/master/
    """

    def __init__(self, response_handler=None, url=None):
        """Initialize this object, collecting base URL from config file.

        If no response handler is specified, use the `code_handler` which will
        raise an exception for 'bad' return codes.

        To specify base url with config file, include the following your
        camayoc config file:

            qcs:
              hostname: 'hostname_or_ip_with_port'
        """
        self._cfg = config.get_config()
        qcs_settings = self._cfg.get('qcs')
        self.url = None
        if url:
            self.url = urljoin(url, 'api/v1/')
        if qcs_settings and not url:
            if not qcs_settings.get('hostname'):
                raise exceptions.QCSBaseUrlNotFound(
                    '\n\'qcs\' section specified in camayoc config file, but'
                    ' no \'hostname\' key found.'
                )
            self.url = urljoin(qcs_settings.get('hostname'), 'api/v1/')
        if not self.url:
            raise exceptions.QCSBaseUrlNotFound(
                '\nNo base url was specified to the client'
                '\neither with the url="host" option or with the camayoc'
                ' config file.')
        if 'http' not in self.url:
            raise exceptions.QCSBaseUrlNotFound(
                'A hostname was provided, but we could not use it.'
                '\nValid hostnames start with http:// or https://'
            )
        if response_handler is None:
            self.response_handler = code_handler
        else:
            self.response_handler = response_handler

    def delete(self, endpoint, **kwargs):
        """Send an HTTP DELETE request."""
        url = urljoin(self.url, endpoint)
        return self.request('DELETE', url, **kwargs)

    def get(self, endpoint, **kwargs):
        """Send an HTTP GET request."""
        url = urljoin(self.url, endpoint)
        return self.request('GET', url, **kwargs)

    def head(self, endpoint, **kwargs):
        """Send an HTTP HEAD request."""
        url = urljoin(self.url, endpoint)
        return self.request('HEAD', url, **kwargs)

    def post(self, endpoint, packet, **kwargs):
        """Send an HTTP POST request."""
        url = urljoin(self.url, endpoint)
        return self.request('POST', url, json=packet, **kwargs)

    def put(self, endpoint, packet, **kwargs):
        """Send an HTTP PUT request."""
        url = urljoin(self.url, endpoint)
        return self.request('PUT', url, json=packet, **kwargs)

    def request(self, method, url, **kwargs):
        """Send an HTTP request.

        Arguments passed directly in to this method override (but do not
        overwrite!) arguments specified in ``self.request_kwargs``.
        """
        # The `self.request_kwargs` dict should *always* have a "url" argument.
        # This is enforced by `self.__init__`. This allows us to call the
        # `requests.request` function and satisfy its signature:
        #
        #     request(method, url, **kwargs)
        #
        return self.response_handler(
            self._cfg,
            requests.request(method, url, **kwargs),
        )


class QCS_Client(Client):
    """An even easier client for interacting with the quipucords API.

    This client inherits all methods and fields from api.Client and adds
    more methods that protect the user from having to remember how to form
    the proper relative paths to the different endpoints.

    Example::
        >>> from camayoc import api
        >>> client = api.QCS_Client()
        >>> client.read_host_creds()
    """

    def __init__(self, *args, **kwargs):
        """Set base url and relative paths to API endpoints.

        The call to super will set base url from the camayoc config file,
        as well as set the response_handler that the client will use.
        """
        self.host_cred_path = 'credentials/hosts/'
        super(QCS_Client, self).__init__(*args, **kwargs)

    def create_host_cred(self, packet):
        """Send POST to QCS to create new host credential."""
        return self.post(self.host_cred_path, packet)

    def read_host_creds(self):
        """Send GET request to read all host credentials."""
        return self.get(self.host_cred_path)

    def update_host_cred(self, host_id, packet):
        """Send PUT request to update given host_id with new data."""
        path = urljoin(self.host_cred_path, urljoin(str(host_id), '/'))
        return self.put(path, packet)

    def delete_host_cred(self, host_id):
        """Send DELETE request for host_id to QCS."""
        path = urljoin(self.host_cred_path, '{}/'.format(host_id))
        return self.delete(path)
