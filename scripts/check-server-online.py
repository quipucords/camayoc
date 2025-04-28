"""
Block until server responds.

This script is used by CI to ensure tests are not run while server is starting.
"""

import argparse
import time

import urllib3

from camayoc import api

urllib3.disable_warnings()


class ServerUnavailableException(Exception):
    pass


class UnexpectedStatusCodeException(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(
        prog="check-server-online", description="Block until server responds"
    )
    parser.add_argument(
        "--timeout", default=30, type=int, help="How long to wait before giving up (seconds)"
    )
    args = parser.parse_args()

    start_time = time.monotonic()

    last_exception = None

    while start_time + args.timeout > time.monotonic():
        try:
            api_client = api.Client(response_handler=api.echo_handler, authenticate=False)
            response = api_client.get("v1/ping/")
            if response.status_code == 200:
                return
            raise UnexpectedStatusCodeException(response.status_code)
        except Exception as e:  # noqa: BLE001
            last_exception = e
        time.sleep(0.5)

    raise ServerUnavailableException(
        f"Server did not respond within {args.timeout} seconds.\n"
        f"Last exception is {type(last_exception).__name__}:\n{last_exception}"
    )


if __name__ == "__main__":
    main()
