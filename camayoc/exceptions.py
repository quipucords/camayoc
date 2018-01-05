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


class QCSBaseUrlNotFound(Exception):
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
