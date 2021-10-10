"""Launcher for UOTT."""

import argparse


def parse_cli_args() -> argparse.Namespace:
    """Parse CLI arguments when called from command line."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="UOTT mode", dest="mode")

    proxy = subparsers.add_parser("proxy", help="run UOTT in proxy mode")
    proxy.add_argument("local-udp")
    proxy.add_argument("remote-tcp")

    client = subparsers.add_parser("client", help="run UOTT in client mode")
    client.set_defaults(mode="client")
    client.add_argument("local-tcp")
    client.add_argument("remote-udp")

    return parser.parse_args()


def main() -> None:
    """Entry point for UOTT daemon."""
    opts = parse_cli_args()
    print(opts)


if __name__ == "__main__":
    main()
