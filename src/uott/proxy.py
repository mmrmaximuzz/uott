"""Proxy module for UOTT."""

import logging
import socket

from .utils import EndPoint

LOG = logging.getLogger("proxy")


def _proxy_serve_client(client: socket.socket, remote_ep: EndPoint) -> None:
    raise NotImplementedError


def _proxy_loop(local: socket.socket, remote_ep: EndPoint) -> None:
    """Run proxy loop forever."""
    while True:
        LOG.info("waiting for the client to connect...")
        client, addr = local.accept()

        LOG.info("client %s connected, start proxying", addr)
        _proxy_serve_client(client, remote_ep)


def start_uott_proxy(local_tcp: EndPoint, remote_udp: EndPoint) -> None:
    """Run proxy loop forever."""
    LOG.info("starting UOTT proxy: TCP:%s -> UDP:%s", local_tcp, remote_udp)

    LOG.info("creating local TCP endpoint")
    local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.bind(local_tcp)
    local.listen(1)

    LOG.info("starting proxy loop")
    _proxy_loop(local, remote_udp)
