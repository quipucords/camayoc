# coding=utf-8
"""Unit tests for :mod:`camayoc.cli`."""
import socket
import unittest
from unittest import mock

from plumbum.machines.local import LocalMachine

from camayoc import cli
from camayoc import exceptions
from camayoc import utils


class EchoHandlerTestCase(unittest.TestCase):
    """Tests for :func:`camayoc.cli.echo_handler`."""

    @classmethod
    def setUpClass(cls):
        """Call the function under test, and record inputs and outputs."""
        cls.completed_proc = mock.Mock()
        cls.output = cli.echo_handler(cls.completed_proc)

    def test_input_returned(self):
        """Assert the passed-in ``completed_proc`` is returned."""
        self.assertIs(self.completed_proc, self.output)

    def test_check_returncode(self):
        """Assert ``completed_proc.check_returncode()`` is not called."""
        self.assertEqual(self.completed_proc.check_returncode.call_count, 0)


class CodeHandlerTestCase(unittest.TestCase):
    """Tests for :func:`camayoc.cli.code_handler`."""

    @classmethod
    def setUpClass(cls):
        """Call the function under test, and record inputs and outputs."""
        cls.completed_proc = mock.Mock()
        cls.output = cli.code_handler(cls.completed_proc)

    def test_input_returned(self):
        """Assert the passed-in ``completed_proc`` is returned."""
        self.assertIs(self.completed_proc, self.output)

    def test_check_returncode(self):
        """Assert ``completed_proc.check_returncode()`` is not called."""
        self.assertEqual(self.completed_proc.check_returncode.call_count, 1)


class CompletedProcessTestCase(unittest.TestCase):
    """Tests for :class:`camayoc.cli.CompletedProcess`."""

    def setUp(self):
        """Generate kwargs that can be used to instantiate a completed proc."""
        self.kwargs = {key: utils.uuid4() for key in {"args", "returncode", "stdout", "stderr"}}

    def test_init(self):
        """Assert all constructor arguments are saved as instance attrs."""
        completed_proc = cli.CompletedProcess(**self.kwargs)
        for key, value in self.kwargs.items():
            with self.subTest(key=key):
                self.assertTrue(hasattr(completed_proc, key))
                self.assertEqual(getattr(completed_proc, key), value)

    def test_check_returncode_zero(self):
        """Call ``check_returncode`` when ``returncode`` is zero."""
        self.kwargs["returncode"] = 0
        completed_proc = cli.CompletedProcess(**self.kwargs)
        self.assertIsNone(completed_proc.check_returncode())

    def test_check_returncode_nonzero(self):
        """Call ``check_returncode`` when ``returncode`` is not zero."""
        self.kwargs["returncode"] = 1
        completed_proc = cli.CompletedProcess(**self.kwargs)
        with self.assertRaises(exceptions.CalledProcessError):
            completed_proc.check_returncode()

    def test_can_eval(self):
        """Assert ``__repr__()`` can be parsed by ``eval()``."""
        string = repr(cli.CompletedProcess(**self.kwargs))
        from camayoc.cli import CompletedProcess  # noqa pylint:disable=unused-variable

        # pylint:disable=eval-used
        self.assertEqual(string, repr(eval(string)))


class ClientTestCase(unittest.TestCase):
    """Tests for :class:`camayoc.cli.Client`."""

    def test_explicit_local_transport(self):
        """Assert it is possible to explicitly ask for a "local" transport."""
        system = cli.System(hostname=utils.uuid4(), transport="local")
        self.assertIsInstance(cli.Client(system).machine, LocalMachine)

    def test_implicit_local_transport(self):
        """Assert it is possible to implicitly ask for a "local" transport."""
        system = cli.System(hostname=socket.getfqdn(), transport=None)
        self.assertIsInstance(cli.Client(system).machine, LocalMachine)

    def test_explicit_ssh_transport(self):
        """Assert it is possible to explicitly ask for a "ssh" transport."""
        system = cli.System(hostname=utils.uuid4(), transport="ssh")
        with mock.patch("camayoc.cli.plumbum.machines.SshMachine") as SshMachine:
            machine = mock.Mock()
            SshMachine.return_value = machine
            self.assertIs(cli.Client(system).machine, machine)

    def test_default_response_handler(self):
        """Assert the default response handler checks return codes."""
        system = cli.System(hostname=utils.uuid4(), transport="local")
        self.assertIs(cli.Client(system).response_handler, cli.code_handler)

    def test_explicit_response_handler(self):
        """Assert it is possible to explicitly set a response handler."""
        system = cli.System(hostname=utils.uuid4(), transport="local")
        handler = mock.Mock()
        self.assertIs(cli.Client(system, handler).response_handler, handler)
