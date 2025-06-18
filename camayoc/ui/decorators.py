import logging
import warnings
from functools import wraps

from camayoc.exceptions import IncorrectDecoratorUsageWarning
from camayoc.types.ui import HistoryRecord
from camayoc.types.ui import Session

logger = logging.getLogger(__name__)


def service(func):
    """Mark method as a service.

    Service is user-facing API that makes tests more concise and faster to develop.
    The idea is that service expresses user *intent*.
    So Credentials page exposes "add_credential" service. How exactly this is done
    is irrelevant and may change. By using services, tests remain relatively stable
    (as long as application is relatively stable).

    We want to mark functions as services, so long-running tester can skip and focus
    on finer-granular actions.
    """
    func.__hvat_hide_method__ = True

    @wraps(func)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner


def record_action(func):
    """Save a function call in session history.

    The idea is that if long-running tester fails, we can catch exception
    and save recorded actions somewhere. So it's easy to investigate what
    it did and when.

    Ideally, we would also have tape playback where we could give a history
    and let tester run it automatically. Which might be useful for debugging,
    setting up environments etc.

    This *could* be moved to metaclass, as we want to record
    most of actions anyway.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        logger.debug(
            "Executing page action [class='%s' action_name='%s' args=%s kwargs=%s]",
            type(args[0]).__name__,
            func.__name__,
            args[1:],
            kwargs,
        )
        page = func(*args, **kwargs)

        try:
            session: Session = page._client.session
        except AttributeError:
            msg = (
                "{}.{}() returned an object of type '{}' which does not implement UIPage "
                "interface.\nAction has not been saved in session history.\n"
                "This is probably a bug, please review your usage of 'record_action' decorator."
            ).format(
                type(args[0]).__name__,
                func.__name__,
                type(page).__name__,
            )
            warnings.warn(msg, category=IncorrectDecoratorUsageWarning)
            return page

        start_page = session.last_record()
        if start_page:
            start_page = start_page.end_page
        else:
            start_page = "<begin navigation>"

        record = HistoryRecord(
            start_page=start_page,
            action=func.__name__,
            args=str(args[1:]),
            kwargs=str(kwargs),
            end_page=type(page).__name__,
        )
        session.add_record(record)
        return page

    return inner


def creates_toast(func):
    """Mark method as one that may create toast notification.

    Run function as usual, but if returned object has _dismiss_notifications
    method (inherited from ToastNotifications) and client is set to
    automatically dismiss notifications, then dismiss notifications.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        page = func(*args, **kwargs)
        if getattr(page, "_dismiss_notifications") and page._client._auto_dismiss_notification:
            page._dismiss_notifications(ensure_notifications_appeared=True)

        return page

    return inner
