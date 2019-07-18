# coding=utf-8
"""Utility functions for yupana tests."""


import base64
import json
import multiprocessing as mp
import re
import requests
import time

from datetime import datetime
from functools import partial
from itertools import chain

from oc import login, get_pods

from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError


def yupana_configs():
    """Return all of the yupana config values"""
    try:
        yupana_configs = get_config().get("yupana", [])
    except ConfigFileNotFoundError:
        yupana_configs = []
    return yupana_configs


def get_x_rh_identity(account_num, org_id):
    """Return the base64 encoded x-rh-identity string from credentials."""
    login_data = {
        "identity": {"account_number": account_num, "internal": {"org_id": org_id}}
    }
    json_str = json.dumps(login_data)
    return base64.b64encode(json_str.encode("ascii"))


def get_app_url(protocol="http://"):
    """Build and return the URI from the config to access the yupana API"""
    yupana_config = yupana_configs()
    config = yupana_config["yupana-app"]
    required_configs = (
        "app_name",
        "openshift_project",
        "openshift_app_domain",
        "api_path",
    )
    if set(required_configs).issubset(set(config.keys())):
        url = (
            protocol
            + config["app_name"]
            + "-"
            + config["openshift_project"]
            + "."
            + config["openshift_app_domain"]
            + config["api_path"]
        )
        return url
    else:
        return None


def post_file(
    file_src,
    api_url,
    rh_username,
    rh_pass,
    x_rh_identity,
    x_rh_insights_request_id,
    file_type="application/vnd.redhat.qpc.tar+tgz",
):
    """Send a file/package up to the cluster."""

    headers = {
        "x-rh-insights-request-id": x_rh_insights_request_id,
        "x-rh-identity": x_rh_identity,
    }

    files = {"file": (file_src, open(file_src, "rb"), file_type)}
    api_endpoint = api_url + "/upload"
    response = requests.post(
        api_endpoint,
        headers=headers,
        files=files,
        auth=(rh_username, rh_pass),
        verify=False,
    )
    return response


def oc_setup():
    """Login to the cluster with oc."""
    yupana_config = yupana_configs()
    oc_config = yupana_config["oc"]
    response = login(oc_config["url"], oc_config["token"])
    return response


def get_app_pods(name, include_builders=False):
    """Get the pod names using the oc_get_pod output."""
    exp = re.compile(f"({name})-(\d+)-(\w+)")
    pod_list = get_pods()
    pod_data = []
    for pod_line in pod_list:
        pod_info = pod_line.split()
        name_match = re.search(exp, pod_info[0])
        if name_match and (include_builders or name_match.group(3) != 'build'):
            pod_data.append(pod_info)
    return pod_data


def get_timestamp(string, regex="(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})"):
    """Matches and grabs the timestmp from a string."""
    exp = re.compile(regex)
    match = re.match(exp, string)
    print(match)
    if match:
        year = int(match.groups()[0])
        month = int(match.groups()[1])
        day = int(match.groups()[2])
        hour = int(match.groups()[3])
        min = int(match.groups()[4])
        sec = int(match.groups()[5])
        return datetime(year, month, day, hour=hour, minute=min,
                        second=sec)
    else:
        return None

def search_log(log_list, search_string):
    """Search through a log list for lines containing the `search_string`.
        Returns a list of the matched lines."""
    return [log_line for log_line in log_list if search_string in log_line]


def search_pods_logs(pods_logs, search_string, pool_size=4):
    """Search through the logs of each pod, and return the combined list."""
    search_func = partial(search_log, rch_log(pod_log, }")
    with mp.Pool(pool_size) as p:
        search_results = p.map(search_func, pods_logs)
    return list(chain(search_results))


def filter_log(log_list, date_min=None, date_max=None, filter_regex=None,
               date_regex="(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})"):
    """Filters log by date range and/or regex matching."""
    if filter_regex:
        match_filter = re.compile(filter_regex)
    filtered_log = []
    for log_line in log_list:
        date_check = True
        filter_check = True
        if date_min or date_max:
            print('date check')
            date_match = get_timestamp(log_line, regex=date_regex)
            if date_match:
                date_check = check_date_range(date_match, date_min, date_max)
            else:
                date_check = False
        if filter_regex:
            print('filter check')
            match = re.mach(match_filter, log_line)
            if not match:
                filter_check: False
        if date_check and filter_check:
            print("Adding: " + log_line)
            filtered_log.append(log_line)

    return(filtered_log)


def check_date_range(date, date_min, date_max):
    """Checks for a date match, and does a comparison to see if the date fits
    inside the range."""
    if date_min and date_max:
        assert date_min <= date_max, "Min date is not less than max date."
    min_check = True
    max_check = True
    if date_min and date < date_min:
        min_check = False
    if date_max and date > date_max:
        max_check = False
    if min_check and max_check:
        return(True)
    else:
        return(False)

def time_diff(start_time):
    """Returns the int of differance (ceiling) in seconds from the start time from NOW."""
    return int(time.time() - start_time) + 1
