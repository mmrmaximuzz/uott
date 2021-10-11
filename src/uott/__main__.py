"""Launcher for UOTT."""

import argparse
import logging

from .client import start_uott_client
from .proxy import start_uott_proxy
from .utils import parse_endpoint


def parse_cli_args() -> argparse.Namespace:
    """Parse CLI arguments when called from command line."""
    parser = argparse.ArgumentParser()

    parser.add_argument("mode", choices=("proxy", "client"),
                        help="select a mode for UOTT")
    parser.add_argument("local", help="local endpoint")
    parser.add_argument("remote", help="remote endpoint")

    return parser.parse_args()


def main() -> None:
    """Entry point for UOTT daemon."""
    logging.basicConfig(level=logging.INFO)

    opts = parse_cli_args()
    local = parse_endpoint(opts.local)
    remote = parse_endpoint(opts.remote)

    if opts.mode == "proxy":
        start_uott_proxy(local, remote)
        return

    if opts.mode == "client":
        start_uott_client(local, remote)
        return

    assert opts.mode in ("proxy", "client")


if __name__ == "__main__":
    main()
