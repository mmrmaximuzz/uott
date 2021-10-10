"""Client module for UOTT."""

import logging
import socket
from itertools import count
from typing import Dict

from .utils import EndPoint

LOG = logging.getLogger("client")


def _client_loop(client: socket.socket, proxy: socket.socket) -> None:
    """Run client loop forever."""
    # prepare mappings for client endpoints
    lasttag = count()
    dirmap: Dict[EndPoint, int] = {}
    revmap: Dict[int, EndPoint] = {}

    while True:
        data, endpoint = client.recvfrom(65535)
        if endpoint not in dirmap:
            LOG.info("new client endpoint: %s", endpoint)
            tag = next(lasttag)
            dirmap[endpoint] = tag
            revmap[tag] = endpoint

        proxy.sendall(f"{tag}".encode() + b":" + data)

    print(data)


def start_uott_client(local_udp: EndPoint, remote_tcp: EndPoint) -> None:
    """Start UOTT client."""
    LOG.info("starting UOTT client: UDP:%s -> TCP:%s", local_udp, remote_tcp)

    LOG.info("connecting to the remote TCP endpoint")
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.connect(remote_tcp)

    LOG.info("creating the local UDP endpoint")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(local_udp)

    LOG.info("starting client loop")
    _client_loop(client, proxy)
