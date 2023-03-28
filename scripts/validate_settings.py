#!/usr/bin/env python3
import argparse
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from camayoc.config import get_settings


def main():
    parser = argparse.ArgumentParser(description="Camayoc configuration file validator")
    parser.add_argument(
        "--file",
        required=True,
        default=None,
        action="store",
        dest="file",
        type=str,
        help="Path to file that will be validated",
    )
    args = parser.parse_args()

    get_settings(args.file)
    print("The file is valid")


if __name__ == "__main__":
    main()
