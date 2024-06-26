"""Test utilities for quipucords' UI tests."""

import pytest

from camayoc.config import settings
from camayoc.ui import Client as UIClient
from camayoc.ui.session import BasicSession


def pytest_exception_interact(node, call, report):
    ui_client = node.funcargs.get("ui_client", None)
    if not ui_client:
        return
    print("List of previous successfull actions:")
    zeroes = len(str(len(ui_client.session.history)))
    for step, record in enumerate(ui_client.session.history):
        step_num = str(step).zfill(zeroes)
        print(f"{step_num}: {record}")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    extra_context_args = {}
    verify_ssl = settings.quipucords_server.ssl_verify
    if not verify_ssl:
        extra_context_args["ignore_https_errors"] = True

    return {**browser_context_args, **extra_context_args}


@pytest.fixture
def ui_client(page):
    client_session = BasicSession()
    client = UIClient(driver=page, session=client_session)
    yield client
    if client.page_errors:
        fail_msg = ["Browser encountered errors during test execution:"]
        page_errors = [f"- {err}" for err in client.page_errors]
        fail_msg = "\n".join(fail_msg + page_errors)
        pytest.fail(fail_msg)
