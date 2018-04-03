# coding=utf-8
"""Tests for ``Reports`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""

import pytest

from camayoc.qcs_models import Report
from camayoc.tests.qcs.api.v1.conftest import SCAN_DATA


@pytest.mark.skip
def test_network(shared_client, cleanup, source):
    """Confirm that reports are generated from network scans.

    :id: 49cbba28-aa3c-425b-ad6a-1acf28530f81
    :description: If a scan successfully generated fingerprints,
        a report should be available associated with the fact
        collection.
    :steps:
        1) Create a network source and associated credential
        2) Create a scan of the sources
        3) Assert that a report is available if the fingerprint was created.
    :expectedresults: If a fingerprint can be made, a report is generated
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_vcenter(shared_client, cleanup, source):
    """Confirm that reports are generated from vcenter scans.

    :id: 7636b041-35d3-41d5-a37b-da645bd8356a
    :description: If a scan successfully generated fingerprints,
        a report should be available associated with the fact
        collection.
    :steps:
        1) Create a vcenter source and associated credential
        2) Create a scan of the sources
        3) Assert that a report is available if the fingerprint was created.
        4) Assert that the following facts are present:

            * cluster name
            * number of vmware hosts in cluster
            * virtual sockets
            * UUID (must be BIOS UUID)
            * MAC address of interfaces
            * Hostname
            * IP address - note systems can have multiple IPs and could
              potentially have the same IP as another system (NAT
              environments)

    :expectedresults: If a fingerprint can be made, a report is generated
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_satellite(shared_client, cleanup, source):
    """Confirm that reports are generated from satellite scans.

    :id: bcbb79d2-5963-4baf-87a4-1fd7861ae8f2
    :description: If a scan successfully generated fingerprints,
        a report should be available associated with the fact
        collection.
    :steps:
        1) Create a satellite source and associated credential
        2) Create a scan of the sources
        3) Assert that a report is available if the fingerprint was created.
        4) Assert that the following facts are present:

            * Name (appears to be hostname)
            * Subscription Name (string title of subscription)
            * Amount (of subscription)
            * Account #
            * Contract #
            * Start Date
            * End Date
            * BIOS Vendor
            * BIOS Version
            * BIOS Release Date
            * System Manufacturer
            * System Product Name
            * Serial Number
            * UUID
            * Chassis Manufacturer
            * Type
            * Chassis Serial #
            * Chassis Product Name

    :expectedresults: If a fingerprint can be made, a report is generated and
        contains expected facts.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_merge_network(shared_client, cleanup, source):
    """Confirm that reports merge facts from network sources.

    :id: 17cdb5ad-f083-471f-92e2-42f7a45c1c5a
    :description: If a scan hits an entity multiple times in a single scan
        job, it should merge the results in the report.
    :steps:
        1) Create a source and associated credential that specifies the same
           machine with multiple IPs
        2) Create a source that specifies the machine just once
        3) Create scans of the sources
        4) Assert that the reports are the same, as the one that hit
           the machine multiple times should have merged the results
    :expectedresults: Scan job results are merged into a report.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_merge_vcenter(shared_client, cleanup, source):
    """Confirm that reports merge facts from vcenter sources.

    :id: 5870750b-5eea-4e24-a720-21d5b33bca82
    :description: If a scan finds the same machine  multiple times in a single
        scan job from vcenter sources it should merge the results in the
        report.
    :steps:
        1) Create multiple vcenter sources using the same vcenter
        2) Create a scan that just scans the source once
        3) Create a scan that scans all the sources (hitting the vcenter
           multiple times.)
        4) Assert that the report has the same number of machines as
           it would have if it only scanned once.
    :expectedresults: Scan job results are merged into a report.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_merge_types(shared_client, cleanup, source):
    """Confirm that reports merge facts from all combinations of types.

    :id: 9958509b-47a1-4d23-889f-9e8c067e705c
    :description: If a scan finds the same machine via any combination of a
        satellite source, a vcenter source, and a network source, data
        related to the machine should be merged. This test is parameterized
        on a network source and a vcenter where it is hosted and a satellite
        with which it is registered.
    :steps:
        1) Create sources for all types used in permutation.
        2) Create scan that uses all sources
        3) Assert that no machine is reported twice
    :expectedresults: Scan job results are merged into a report.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_redact(shared_client, cleanup, source):
    """Confirm that I can request that facts be redacted in the report.

    :id: 316554c3-d98a-46fb-bcad-fd5569bb603d
    :description: A user should be able to query for a redacted report where
        requested facts are obfuscated.
    :steps: This functionality is not yet implemented.
    :expectedresults: I can request that facts are redacted in a report.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_tag_hosts(shared_client, cleanup, source):
    """Confirm that users can tag hosts with additional attributes.

    :id: e9125267-0ea8-42e2-8bef-416bb0b85030
    :description: Test that a user may somehow "tag" hosts with some kind of
        "exclude" attribute so it can be excluded from Density and Time Series
        reports.
    :steps: This functionality is not yet implemented.
    :expectedresults: Users have the ability to tag hosts with user defined
        attributes and these can be used to change how reports are generated.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_density_report(shared_client, cleanup, source):
    """Test that I may request a Denisty Report for each product.

    :id: 23ab889b-3c47-42e6-a9db-288bde926c48
    :description: For each product, I should be able to get a report from a
        scan detailing how many machines were found with specified product.
        Density reports should contain the following information:

            * number of hosts
            * number of virtual cores
            * number of physical cores
            * number of sockets
            * number of socket pairs
            * Version of product
            * Report includes sum of virtual cores
            * Report includes sum  of physical cores
            * Report includes sum of sockets
            * Report includes sum of socket pairs
            * Report correctly differentiates between redhat and community
              versions of product
            * Report deduces from raw facts definitive version of rhel and
              when it cannot deduce definitive version, it indicates this in
              some way
            * Report shows id of fact collection sourced from

    :steps: This functionality is not yet implemented.
    :expectedresults: Density reports provide data only about machines with
        requested product.
    :caseautomation: notautomated
    """


@pytest.mark.skip
def test_time_series(shared_client, cleanup, source):
    """Test that a user can request a time series report.

    :id: 06823f56-760a-412f-b0a5-c33a19f511ca
    :description: Test that for each product, I can generate a report that
        takes in many fact collections given a start date and end date and
        source and produces a report that shows how many {hosts, physical
        cores, sockets, socket pairs, virtual cores} were found with that
        product at each scan. Must allow some definition of “step value”,
        i.e. period between fact collections to include.

    :steps: This functionality is not yet implemented.
    :expectedresults: Users can generate a time series report.
    :caseautomation: notautomated
    """


def test_merge_reports_from_scanjob():
    """Confirm that a report is created from valid scan job identifiers.

    :id: 10c6b86a-4271-4b00-b9bb-4ff4a37bb02c
    :description: If two valid scan job identifiers are provided,
        a valid report identifier should be returned.
    :steps:
        1) Grab the scan info for the scans to merge from SCAN_DATA
        2) Check if the scan info is None for either scan and return if so
        3) Grab the scan job identifier from the scan info of each scan
        4) Create a report object & merge the scan job identifiers
        5) Access the deployments & details endpoint of the report
        6) Assert that all response codes were successful
    :expectedresults: Scan job results are merged into a report.
    """
    errors_found = []
    scan1 = SCAN_DATA.get('non-rhel')
    scan2 = SCAN_DATA.get('rhel-7')
    # if either scan is None, they were not in the config file or the
    # tests have been ran with RUN_SCANS=False and there are no scan results
    if scan1 is None or scan2 is None:
        return
    id1 = scan1.get('scan_job_id')
    id2 = scan2.get('scan_job_id')
    report = Report()
    response = report.merge([id1, id2])
    summary = report.summary()
    details = report.details()
    status_codes = [response.status_code, summary.status_code,
                    details.status_code]
    error = False
    for code in status_codes:
        if code not in range(200, 203):
            error = True
    if error:
        errors_found.append(
            'Merging scan jobs with identifiers: {scan1_id}, {scan2_id}'
            'resulted in a failed merge report. The report returned a status '
            'code of {report_status}. The summary endpoint returned a status '
            'code of {summary_status}. The details endpoint returned a status '
            'code of {details_status}.'.format(
                scan1_id=id1, scan2_id=id2,
                report_status=response.status_code,
                summary_status=summary.status_code,
                details_status=details.status_code)
        )
    assert len(errors_found) == 0, '\n================\n'.join(errors_found)


def test_merge_reports_negative():
    """Confirm that merging invalid scan job ids does not result in a report.

    :id: 552e5de4-3697-11e8-b467-0ed5f89f718b
    :description: If a merge is attempted with invalid scan job identifiers,
        then report is not created.
    :steps:
        1) Create a list of invalid identifiers for merge requests
        2) Grab the connection scan from the SCAN_DATA
        3) Grab the unreachable scan from the SCAN_DATA
        4) Check that both the connection & unreachable scan exist
        5) If they do, grab the scan job identifiers and add them to the list
            of invalid identifiers
        6) Loop through the invalid ids and assert that each merge fails
    :expectedresults: A report is not created from invalid ids.
    """
    errors_found = []
    # create a list of invalid options for merging scan job identifiers
    invalid_ids = [[1], [1, 1], ['one', 'one'], []]
    # attempt to grab the connection_scan & unreachable scan from data
    connection_scan = SCAN_DATA.get('Connection')
    unreachable_scan = SCAN_DATA.get('Unreachable')
    if connection_scan and unreachable_scan:
        # if the info was found, grab the ids from the data and add them
        # to the list of invalid identifiers
        connection_id = connection_scan.get('scan_job_id')
        unreachable_id = unreachable_scan.get('scan_job_id')
        invalid_ids.append([connection_id, unreachable_id])
    report = Report()
    # Loop through the invalid ids and assert that the merge fails
    for ids in invalid_ids:
        errors_found = report.assert_merge_fails(ids, errors_found)
    assert len(errors_found) == 0, '\n================\n'.join(errors_found)
