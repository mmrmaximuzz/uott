"""Proxy module for UOTT."""

import contextlib
import logging
import selectors
import socket
from typing import Dict

from .protocol import deserialize, StreamTransformer
from .utils import EndPoint

LOG = logging.getLogger("proxy")


class _ClientDisconnected(Exception):
    """Raise this exception to break server loop on client disconnect."""


def _process_client(client: socket.socket, remote_ep: EndPoint,
                    tagmap: Dict[int, socket.socket],
                    revmap: Dict[socket.socket, int],
                    selector: selectors.DefaultSelector,
                    deserializer: StreamTransformer) -> None:
    """Process TCP flow from the client."""
    with contextlib.suppress(BlockingIOError):
        while True:
            chunk = client.recv(4096, socket.MSG_DONTWAIT)
            if not chunk:
                raise _ClientDisconnected

            msgs = deserializer.send(chunk)
            for tag, dgram in msgs:
                if tag not in tagmap:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.bind(("127.0.0.1", 0))  # TODO: take bind IP from CLI
                    tagmap[tag] = sock
                    revmap[sock] = tag
                    selector.register(sock, selectors.EVENT_READ)
                    LOG.info("proxying new UDP socket: %s", sock.getsockname())

                sock = tagmap[tag]
                sock.sendto(dgram, remote_ep)


def _proxy_serve_client(client: socket.socket, remote_ep: EndPoint) -> None:
    """Run new proxy session."""
    # prepare mappings for local UDP endpoints
    tagmap: Dict[int, socket.socket] = {}
    revmap: Dict[socket.socket, int] = {}

    # put the initial client socket in a new selector
    sel = selectors.DefaultSelector()
    sel.register(client, selectors.EVENT_READ)

    # prepare stream transformer for TCP flow
    deserializer = deserialize()
    deserializer.send(None)

    while True:
        events = sel.select()
        for key, _ in events:
            if key.fileobj is client:
                _process_client(client, remote_ep,
                                tagmap, revmap,
                                sel, deserializer)
            else:
                sock = key.fileobj
                assert sock in revmap, "corrupted selector"

                _process_remote(sock, client, remote_ep, revmap)


def _proxy_loop(local: socket.socket, remote_ep: EndPoint) -> None:
    """Run proxy loop forever."""
    while True:
        LOG.info("waiting for the client to connect...")
        client, addr = local.accept()

        LOG.info("client %s connected, start proxying", addr)
        with contextlib.suppress(_ClientDisconnected):
            _proxy_serve_client(client, remote_ep)

        LOG.info("client %s disconnected, stop proxying")


def start_uott_proxy(local_tcp: EndPoint, remote_udp: EndPoint) -> None:
    """Run proxy loop forever."""
    LOG.info("starting UOTT proxy: TCP:%s -> UDP:%s", local_tcp, remote_udp)

    LOG.info("creating local TCP endpoint")
    local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.bind(local_tcp)
    local.listen(1)

    LOG.info("starting proxy loop")
    with contextlib.suppress(KeyboardInterrupt):
        _proxy_loop(local, remote_udp)

    LOG.info("\nInterrupted, closing")
