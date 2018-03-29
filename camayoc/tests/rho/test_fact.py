# coding=utf-8
"""Tests for ``rho fact`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""
import csv
import hashlib
import random
from collections import OrderedDict
from io import BytesIO

import pexpect

import pytest

from camayoc import utils
from camayoc.constants import (
    RHO_ALL_FACTS,
    RHO_CONNECTION_FACTS,
    RHO_JBOSS_ALL_FACTS,
    RHO_JBOSS_FACTS,
)


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
    rho_fact_list.logfile.close()
    rho_fact_list.close()
    assert rho_fact_list.exitstatus == 0
    facts = [line.split(' - ')[0].strip() for line in output.splitlines()]
    assert sorted(facts) == sorted(RHO_ALL_FACTS)


def test_fact_list_filter():
    """Filter the list of available facts.

    :id: 1f62097a-3ea5-453a-a9e7-0da3cb48def5
    :description: Filter the list of available facts by providing the
        ``--filter`` option.
    :steps: Run ``rho fact list --filter <filter>``
    :expectedresults: Only the facts that match the filter are printed.
    """
    facts = random.choice((
        RHO_CONNECTION_FACTS,
        RHO_JBOSS_FACTS + RHO_JBOSS_ALL_FACTS,
    ))
    fact_filter = facts[0].split('.')[0]
    rho_fact_list = pexpect.spawn(
        'rho fact list --filter {}'.format(fact_filter))
    rho_fact_list.logfile = BytesIO()
    rho_fact_list.expect(pexpect.EOF)
    output = rho_fact_list.logfile.getvalue().decode('utf-8')
    assert len(output.splitlines()) == len(facts)
    for fact in facts:
        assert fact in output
    rho_fact_list.logfile.close()
    rho_fact_list.close()
    assert rho_fact_list.exitstatus == 0


def test_fact_list_regex_filter():
    """Use a regex to filter the list of available facts.

    :id: c4843f39-5c16-4154-9221-5e222fb6e4d5
    :description: Filter the list of available facts by providing the
        ``--filter`` option with a regular expression as a value.
    :steps: Run ``rho fact list --filter <regex_filter>``
    :expectedresults: Only the facts that match the regex filter are printed.
    """
    expected_facts = (
        'subman.virt.host_type',
        'virt-what.type',
        'virt.type',
    )
    rho_fact_list = pexpect.spawn(
        'rho fact list --filter {}'.format(r'"[\w.-]+type"'))
    rho_fact_list.logfile = BytesIO()
    rho_fact_list.expect(pexpect.EOF)
    output = rho_fact_list.logfile.getvalue().decode('utf-8')
    rho_fact_list.logfile.close()
    rho_fact_list.close()
    assert rho_fact_list.exitstatus == 0

    facts = [line.split(' - ')[0].strip() for line in output.splitlines()]
    assert sorted(facts) == sorted(expected_facts)


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


@pytest.mark.parametrize('facts_value', ('file', 'string'))
def test_fact_hash_with_facts(isolated_filesystem, facts_value):
    """Hash only the specified facts from a generated report.

    :id: 3ae721ff-f910-4f09-971e-bf96d0832df5
    :description: Hash only the specified facts from a generated report.
    :steps: Run ``rho fact hash --facts <facts> --reportfile <reportfile>
        --outputfile <outputfile>``
    :expectedresults: Only the specified facts are hashed.
    """
    facts = OrderedDict({
        'connection.host': utils.uuid4(),
        'connection.port': utils.uuid4(),
        'uname.all': utils.uuid4(),
        'uname.hostname': utils.uuid4(),
    })
    facts_to_hash = [
        'connection.host',
        'connection.port',
    ]
    reportfile = utils.uuid4()
    outputfile = utils.uuid4()
    with open(reportfile, 'w') as f:
        f.write(','.join(facts.keys()) + '\n')
        f.write(','.join(facts.values()) + '\n')

    if facts_value == 'file':
        facts_value = 'facts_file'
        with open(facts_value, 'w') as handler:
            for fact in facts_to_hash:
                handler.write(fact + '\n')
    else:
        facts_value = ' '.join(facts_to_hash)
    rho_fact_hash = pexpect.spawn(
        'rho fact hash --facts {} --reportfile {} --outputfile {}'
        .format(facts_value, reportfile, outputfile)
    )
    rho_fact_hash.logfile = BytesIO()
    rho_fact_hash.expect(pexpect.EOF)
    output = rho_fact_hash.logfile.getvalue().decode('utf-8')
    assert len(output.splitlines()) == len(facts_to_hash)
    rho_fact_hash.logfile.close()
    rho_fact_hash.close()
    assert rho_fact_hash.exitstatus == 0

    expected_hashed_facts = facts.copy()
    for fact in facts_to_hash:
        expected_hashed_facts[fact] = hashlib.sha256(
            expected_hashed_facts[fact].encode('utf-8')).hexdigest()

    with open(outputfile) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        parsed_facts = rows[0]
        assert parsed_facts == expected_hashed_facts
