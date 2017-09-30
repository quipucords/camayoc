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
    """No base url was specifed in the camayoc config file.

    Specify a base url to contact the quipucords server in your camayoc
    config file in the following manner:

    qcs:
      server: 'hostname_or_ip_with_port'
    """
