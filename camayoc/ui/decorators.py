from functools import wraps


def service():
    """Marks method as a service

    Service is user-facing API that makes tests more concise and faster to develop.
    The idea is that service expresses user *intent*.
    So Credentials page exposes "add_credential" service. How exactly this is done
    is irrelevant and may change. By using services, tests remain relatively stable
    (as long as application is relatively stable).

    We want to mark functions as services, so long-running tester can skip and focus
    on finer-granular actions.
    """


def autofill():
    """Make all arguments optional

    Wrap a function, take all arguments beside `self`, check the type
    and automatically create value conforming to this type. Then call
    the function with generated value.

    If value is provided, don't do anything.

    Expose the same function signature, but with all arguments wrapped
    in `Optional`.

    This way long-running tester can automatically fill forms with random,
    but correct data.

    Test authors may skip arguments and get randomized data each test run,
    or they can opt-in to create argument objects and run the same test
    every time. May be useful for edge cases!
    """


def record_action():
    """Save a function call in session history

    The idea is that if long-running tester fails, we can catch exception
    and save recorded actions somewhere. So it's easy to investigate what
    it did and when.

    Ideally, we would also have tape playback where we could give a history
    and let tester run it automatically. Which might be useful for debugging,
    setting up environments etc.

    This *could* be movd to metaclass, as we want to record
    most of actions anyway.
    """


def creates_toast(func):
    """Marks method as one that may create toast notification

    Run function as usual, but if return object has _dismiss_notifications
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
