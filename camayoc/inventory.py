# coding=utf-8
"""Host Based Inventory (HBI) API."""
import requests
import urllib3

INVENTORY_HOSTS_PATH = "/hosts"
"""The path to the endpoint used for obaining hosts facts."""


# Suppress HTTPS warnings against our test server without a cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _request(method, url, **kwargs):
    response = requests.request(method, url, **kwargs)
    return response


def _parse_response(response, cond=lambda status: 200 <= status < 400):
    if cond(response.status_code):
        return True, response.json()
    return False, response.text


def client(url, auth, x_rh_identity=None, method="get", cond=lambda status: 200 <= status < 400):
    """Simple REST API client."""
    headers = {}
    if x_rh_identity:
        headers = x_rh_identity
    in_pagination = True
    params = {}
    count = 0
    results = []
    while in_pagination:
        response = _request(method, url, auth=auth, params=params, headers=headers, verify=False)
        ok, info = _parse_response(response, cond)
        if not ok:
            raise RuntimeError(info)
        count += info["count"]
        if info["total"] <= count:
            in_pagination = False
        else:
            page = info["page"] + 1
            params = {"page": page}
        results.extend(info["results"])
    return results


def get_hosts(api_url, auth=None, x_rh_identity=None):
    """Read the entire list of hosts."""
    url = f"{api_url}/{INVENTORY_HOSTS_PATH}"
    results = client(url, auth, x_rh_identity, "get", lambda status: status == 200)
    return results


def find_hosts(host_id_list, api_url, auth=None, x_rh_identity=None):
    """Find one or more hosts by their ID."""
    hosts = ",".join(host_id_list)
    url = f"{api_url}/{INVENTORY_HOSTS_PATH}/{hosts}"
    results = client(url, auth, x_rh_identity, "get", lambda status: status == 200)
    return results
