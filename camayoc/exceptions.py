# coding=utf-8
"""Custom exceptions defined by Camayoc."""


class CalledProcessError(Exception):
    """Indicates a CLI process has a non-zero return code.

    See :meth:`camayoc.cli.CompletedProcess` for more information.
    """

    def __str__(self):
        """Provide a human-friendly string representation of this exception."""
        return (
            'Command {} returned non-zero exit status {}.\n\n'
            'stdout: {}\n\n'
            'stderr: {}'
        ).format(*self.args)


class ConfigFileNotFoundError(Exception):
    """We cannot find the requested Camayoc configuration file.

    See :mod:`camayoc.config` for more information on how configuration files
    are handled.
    """


class QPCBaseUrlNotFound(Exception):
    """Was not able to build a base URL with the config file information.

    Check the expected configuration file format on the API Client
    documentation.
    """


class WaitTimeError(Exception):
    """A task has raised this error because it has been waiting too long.

    A task was waiting for a long running task, but it has exceeded the time
    allowed. Instead of allowing the task to hang, it has aborted and raised
    this error.
    """


class FailedScanException(Exception):
    """A test has raised this exception because a scan failed.

    While waiting for the scan to acheive some other state, the scan failed.
    The test expected the scan to succeed, so this exception has been raised.
    """


class StoppedScanException(Exception):
    """A test has raised this exception because a scan unexpectly stopped.

    While waiting for the scan to achieve some other state, the scan reached
    a terminal state from which it could not progress, so this exception has
    been raised instead of continuing to wait.
    """
