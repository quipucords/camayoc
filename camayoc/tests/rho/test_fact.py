# coding=utf-8
"""Tests for ``rho fact`` commands.

:caseautomation: automated
:casecomponent: fact
:caseimportance: high
:requirement: RHO
:testtype: functional
:upstream: yes
"""
import csv
import hashlib
from collections import OrderedDict
from io import BytesIO

import pexpect

from camayoc import utils


def test_fact_list():
    """List the available facts.

    :id: ba86cfcd-e1e1-49e5-bb36-2c294dbd02cc
    :description: List the available facts.
    :steps: Run ``rho fact list``
    :expectedresults: All the available facts are printed.
    """
    rho_fact_list = pexpect.spawn('rho fact list')
    rho_fact_list.logfile = BytesIO()
    rho_fact_list.expect(pexpect.EOF)
    output = rho_fact_list.logfile.getvalue().decode('utf-8')
    assert len(output.splitlines()) == 60
    rho_fact_list.logfile.close()
    rho_fact_list.close()
    assert rho_fact_list.exitstatus == 0


def test_fact_list_filter():
    """Filter the list of available facts.

    :id: 1f62097a-3ea5-453a-a9e7-0da3cb48def5
    :description: Filter the list of available facts by providing the
        ``--filter`` option.
    :steps: Run ``rho fact list --filter <filter>``
    :expectedresults: Only the facts that match the filter are printed.
    """
    rho_fact_list = pexpect.spawn('rho fact list --filter connection')
    rho_fact_list.logfile = BytesIO()
    rho_fact_list.expect(pexpect.EOF)
    output = rho_fact_list.logfile.getvalue().decode('utf-8')
    assert len(output.splitlines()) == 3
    for fact in ('connection.port', 'connection.port', 'connection.uuid'):
        assert fact in output
    rho_fact_list.logfile.close()
    rho_fact_list.close()
    assert rho_fact_list.exitstatus == 0


def test_fact_hash(isolated_filesystem):
    """Hash some facts from a generated report.

    :id: c8f16fd6-1c2f-47ec-840b-7b8bf6b9c1bb
    :description: Hash some facts from a generated report.
    :steps: Run ``rho fact hash --reportfile <reportfile> --outputfile
        <outputfile>``
    :expectedresults: Only the expected facts are hashed.
    """
    facts_to_hash = OrderedDict({
        'connection.host': utils.uuid4(),
        'connection.port': utils.uuid4(),
        'uname.all': utils.uuid4(),
        'uname.hostname': utils.uuid4(),
    })
    reportfile = utils.uuid4()
    outputfile = utils.uuid4()
    with open(reportfile, 'w') as f:
        f.write(','.join(facts_to_hash.keys()) + '\n')
        f.write(','.join(facts_to_hash.values()) + '\n')
    rho_fact_hash = pexpect.spawn(
        'rho fact hash --reportfile {} --outputfile {}'
        .format(reportfile, outputfile)
    )
    rho_fact_hash.logfile = BytesIO()
    rho_fact_hash.expect(pexpect.EOF)
    output = rho_fact_hash.logfile.getvalue().decode('utf-8')
    assert len(output.splitlines()) == 4
    rho_fact_hash.logfile.close()
    rho_fact_hash.close()
    assert rho_fact_hash.exitstatus == 0

    expected_hashed_facts = {
        k: hashlib.sha256(v.encode('utf-8')).hexdigest()
        for k, v in facts_to_hash.items()
    }
    with open(outputfile) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        parsed_facts = rows[0]
        assert parsed_facts == expected_hashed_facts
