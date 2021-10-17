"""Proxy module for UOTT."""

import contextlib
import logging
import selectors
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, MSG_DONTWAIT
from typing import Dict

from .protocol import deserialize, serialize, StreamTransformer
from .utils import EndPoint

LOG = logging.getLogger("proxy")


class _ClientDisconnected(Exception):
    """Raise this exception to break server loop on client disconnect."""


def _process_client(client: socket, remote_ep: EndPoint,
                    tagmap: Dict[int, socket],
                    revmap: Dict[socket, int],
                    selector: selectors.DefaultSelector,
                    deserializer: StreamTransformer,
                    stack: contextlib.ExitStack) -> None:
    """Process TCP flow from the client."""
    with contextlib.suppress(BlockingIOError):
        while True:
            chunk = client.recv(4096, MSG_DONTWAIT)
            if not chunk:
                raise _ClientDisconnected

            msgs = deserializer.send(chunk)
            for tag, dgram in msgs:
                if tag not in tagmap:
                    sock = stack.enter_context(socket(AF_INET, SOCK_DGRAM))
                    sock.bind(("0.0.0.0", 0))  # TODO: limit to one addr?
                    tagmap[tag] = sock
                    revmap[sock] = tag
                    selector.register(sock, selectors.EVENT_READ)
                    LOG.info("proxying new UDP socket: %s", sock.getsockname())

                sock = tagmap[tag]
                sock.sendto(dgram, remote_ep)


def _process_remote(sock: socket, client: socket,
                    remote_ep: EndPoint, tag: int) -> None:
    """Process messages from the local UDP socket."""
    with contextlib.suppress(BlockingIOError):
        while True:
            dgram, addr = sock.recvfrom(65535, MSG_DONTWAIT)
            if addr != remote_ep:
                # ignore other endpoints' messages
                continue

            msg = serialize((tag, dgram))
            client.sendall(msg)


def _proxy_serve_client(client: socket, remote_ep: EndPoint,
                        stack: contextlib.ExitStack) -> None:
    """Run new proxy session."""
    # prepare mappings for local UDP endpoints
    tagmap: Dict[int, socket] = {}
    revmap: Dict[socket, int] = {}

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
                _process_client(client, remote_ep, tagmap, revmap,
                                sel, deserializer, stack)
            else:
                sock = key.fileobj
                assert sock in revmap, "corrupted selector"

                tag = revmap[sock]
                _process_remote(sock, client, remote_ep, tag)


def _proxy_loop(local: socket, remote_ep: EndPoint) -> None:
    """Run proxy loop forever."""
    while True:
        LOG.info("waiting for the client to connect...")
        sock, addr = local.accept()

        # keep all the session resources in the ExitStack
        with contextlib.ExitStack() as stack:
            client = stack.enter_context(sock)

            LOG.info("client %s connected, start proxying", addr)
            with contextlib.suppress(_ClientDisconnected):
                _proxy_serve_client(client, remote_ep, stack)

            LOG.info("client %s disconnected, stop proxying", addr)


def start_uott_proxy(local_tcp: EndPoint, remote_udp: EndPoint) -> None:
    """Run proxy loop forever."""
    LOG.info("starting UOTT proxy: TCP:%s -> UDP:%s", local_tcp, remote_udp)

    LOG.info("creating local TCP endpoint")
    with socket(AF_INET, SOCK_STREAM) as local:
        local.bind(local_tcp)
        local.listen(1)

        LOG.info("starting proxy loop")
        with contextlib.suppress(KeyboardInterrupt):
            _proxy_loop(local, remote_udp)

        LOG.info("\nInterrupted, closing")
