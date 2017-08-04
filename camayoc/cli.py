# coding=utf-8
"""A client for running local or remote commands."""
import socket
from collections import namedtuple

import plumbum

from camayoc import exceptions


System = namedtuple('System', 'hostname transport')
"""A system representation to run commands on."""


def echo_handler(completed_proc):
    """Immediately return ``completed_proc``."""
    return completed_proc


def code_handler(completed_proc):
    """Check the process for a non-zero return code. Return the process.

    Check the return code by calling ``completed_proc.check_returncode()``.
    See: :meth:`camayoc.cli.CompletedProcess.check_returncode`.
    """
    completed_proc.check_returncode()
    return completed_proc


class CompletedProcess(object):
    """A process that has finished running.

    This class is similar to the ``subprocess.CompletedProcess`` class
    available in Python 3.5 and above. Significant differences include the
    following:

    * All constructor arguments are required.
    * :meth:`check_returncode` returns a custom exception, not
      ``subprocess.CalledProcessError``.

    All constructor arguments are stored as instance attributes.

    :param args: A string or a sequence. The arguments passed to
        :meth:`camayoc.cli.Client.run`.
    :param returncode: The integer exit code of the executed process. Negative
        for signals.
    :param stdout: The standard output of the executed process.
    :param stderr: The standard error of the executed process.
    """

    def __init__(self, args, returncode, stdout, stderr):
        """Initialize a new object."""
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        """Provide an ``eval``-compatible string representation."""
        str_kwargs = ', '.join([
            'args={!r}'.format(self.args),
            'returncode={!r}'.format(self.returncode),
            'stdout={!r}'.format(self.stdout),
            'stderr={!r}'.format(self.stderr),
        ])
        return '{}({})'.format(type(self).__name__, str_kwargs)

    def check_returncode(self):
        """Raise an exception if ``returncode`` is non-zero.

        Raise :class:`camayoc.exceptions.CalledProcessError` if
        ``returncode`` is non-zero.

        Why not raise ``subprocess.CalledProcessError``? Because stdout and
        stderr are not included when str() is called on a CalledProcessError
        object. A typical message is::

            "Command '('ls', 'foo')' returned non-zero exit status 2"

        This information is valuable. One could still make
        ``subprocess.CalledProcessError`` work by overloading ``args``:

        >>> if isinstance(args, (str, bytes)):
        ...     custom_args = (args, stdout, stderr)
        ... else:
        ...     custom_args = tuple(args) + (stdout, stderr)
        >>> subprocess.CalledProcessError(args, returncode)

        But this seems like a hack.

        In addition, it's generally good for an application to raise expected
        exceptions from its own namespace, so as to better abstract away
        dependencies.
        """
        if self.returncode != 0:
            raise exceptions.CalledProcessError(
                self.args,
                self.returncode,
                self.stdout,
                self.stderr,
            )


class Client(object):
    """A convenience object for working with a CLI.

    This class provides the ability to execute shell commands on either the
    local system or a remote system. Here is a pedagogic usage example:

    >>> from camayoc import cli
    >>> system = cli.System(hostname='localhost', transport='local')
    >>> client = cli.Client(system)
    >>> response = client.run(('echo', '-n', 'foo'))
    >>> response.returncode == 0
    True
    >>> response.stdout == 'foo'
    True
    >>> response.stderr == ''
    True

    The above example shows how various classes fit together. It's also
    verbose: smartly chosen defaults mean that most real code is much more
    concise.

    You can customize how ``Client`` objects execute commands and handle
    responses by fiddling with the two public instance attributes:

    ``machine``
        A `Plumbum`_ machine. :meth:`run` delegates all command execution
        responsibilities to this object.
    ``response_handler``
        A callback function. Each time ``machine`` executes a command, the
        result is handed to this callback, and the callback's return value is
        handed to the user.

    If ``system.transport`` is ``local`` or ``ssh``, ``machine`` will be set so
    that commands run locally or over SSH, respectively. If
    ``system.transport`` is ``None``, the constructor will guess how to set
    ``machine`` by comparing the hostname embedded in ``system.hostname``
    against the current system's hostname.  If they match, ``machine`` is set
    to execute commands locally; and vice versa.

    :param camayoc.cli.System system: Information about the system on which
        commands will be executed.
    :param response_handler: A callback function. Defaults to
        :func:`camayoc.cli.code_handler`.

    .. _Plumbum: http://plumbum.readthedocs.io/en/latest/index.html
    """

    def __init__(self, system, response_handler=None):
        """Initialize this object with needed instance attributes."""
        # How do we make requests?
        hostname = system.hostname
        transport = system.transport
        if transport is None:
            transport = 'local' if hostname == socket.getfqdn() else 'ssh'
        if transport == 'local':
            self.machine = plumbum.machines.local
        else:  # transport == 'ssh'
            # The SshMachine is a wrapper around the system's "ssh" binary.
            # Thus, it uses ~/.ssh/config, ~/.ssh/known_hosts, etc.
            self.machine = plumbum.machines.SshMachine(hostname)

        # How do we handle responses?
        if response_handler is None:
            self.response_handler = code_handler
        else:
            self.response_handler = response_handler

    def run(self, args, **kwargs):
        """Run a command and ``return self.response_handler(result)``.

        This method is a thin wrapper around Plumbum's `BaseCommand.run`_
        method, which is itself a thin wrapper around the standard library's
        `subprocess.Popen`_ class. See their documentation for detailed usage
        instructions. See :class:`camayoc.cli.Client` for a usage example.

        .. _BaseCommand.run:
           http://plumbum.readthedocs.io/en/latest/api/commands.html#plumbum.commands.base.BaseCommand.run
        .. _subprocess.Popen:
           https://docs.python.org/3/library/subprocess.html#subprocess.Popen
        """
        # Let self.response_handler check return codes. See:
        # https://plumbum.readthedocs.io/en/latest/api/commands.html#plumbum.commands.base.BaseCommand.run
        kwargs.setdefault('retcode')

        code, stdout, stderr = self.machine[args[0]].run(args[1:], **kwargs)
        completed_process = CompletedProcess(args, code, stdout, stderr)
        return self.response_handler(completed_process)
