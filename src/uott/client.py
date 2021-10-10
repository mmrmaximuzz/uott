"""Client module for UOTT."""

import logging

from .utils import EndPoint

LOG = logging.getLogger("client")


def start_uott_client(local_udp: EndPoint, remote_tcp: EndPoint) -> None:
    """Start UOTT client."""
    LOG.info("starting UOTT client: UDP:%s -> TCP:%s", local_udp, remote_tcp)
