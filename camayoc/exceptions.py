# coding=utf-8
"""Custom exceptions defined by Camayoc."""


class ConfigFileNotFoundError(UserWarning):
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


class ScanJobWithoutReportException(Exception):
    """Raised when trying to obtain report_id from ScanJob that does not have it.

    Raised by Report.retrieve_from_scan_job() when ScanJob does not have report_id
    key. Usually that happens because ScanJob failed.
    """


class MisconfiguredWidgetException(Exception):
    """Raised by UI Widget when expected property is not there."""


class PageFactoryException(Exception):
    """Page factory received invalid value and can't instantiate new class."""


class DataProviderException(Exception):
    """Generic problem raised by DataProvider class."""


class APIResultsEmpty(DataProviderException):
    """API request response results is empty.

    This DataProvider is unable to yield any values.
    """


class NoMatchingDataDefinitionException(DataProviderException):
    """Nothing matches requested definition.

    Requested match_criteria do not match anything in DataProvider
    instance configuration.
    """


class FilteredAPIResultsEmpty(DataProviderException):
    """API didn't return anything matching criteria.

    There are no objects in API request response results matching
    provided criteria.

    This configuration of DataProvider is unable to yield any values.
    """


class IncorrectDecoratorUsageWarning(UserWarning):
    """Decorator was used incorrectly, but error is salvageable."""
