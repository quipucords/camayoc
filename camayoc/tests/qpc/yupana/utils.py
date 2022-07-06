# coding=utf-8
"""Utility functions for yupana tests."""
import re
import time
from datetime import datetime

import requests
from oc import get_pods

# Constants
PATTERN_DATE_TIME = r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})"


# Functions
def get_app_url(yupana_config, protocol="http://"):
    """Build and return the URI from the config to access the yupana API"""
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


def get_app_pods(name, include_builders=False):
    """Get the pod names using the oc_get_pod output."""
    exp = re.compile(r"({name})-(\d+)-(\w+)")
    pod_list = get_pods()
    pod_data = []
    for pod_line in pod_list:
        pod_info = pod_line.split()
        name_match = re.search(exp, pod_info[0])
        if name_match and (include_builders or name_match.group(3) != "build"):
            pod_data.append(pod_info)
    return pod_data


def get_timestamp(string, regex=PATTERN_DATE_TIME):
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
        return datetime(year, month, day, hour=hour, minute=min, second=sec)
    else:
        return None


def filter_log(
    log_list,
    date_min=None,
    date_max=None,
    filter_regex=None,
    date_regex=PATTERN_DATE_TIME,
):
    """Filters log by date range and/or regex matching."""
    if filter_regex:
        match_filter = re.compile(filter_regex)
    filtered_log = []
    for log_line in log_list:
        date_check = True
        filter_check = True
        if date_min or date_max:
            print("date check")
            date_match = get_timestamp(log_line, regex=date_regex)
            if date_match:
                date_check = check_date_range(date_match, date_min, date_max)
            else:
                date_check = False
        if filter_regex:
            print("filter check")
            match = re.mach(match_filter, log_line)
            if not match:
                filter_check: False
        if date_check and filter_check:
            print("Adding: " + log_line)
            filtered_log.append(log_line)

    return filtered_log


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
        return True
    else:
        return False


def time_diff(start_time):
    """Returns the int of differance (ceiling) in seconds from the start time from NOW."""
    return int(time.time() - start_time) + 1
