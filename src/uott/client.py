"""Client module for UOTT."""

import contextlib
import logging
import selectors
import socket
from itertools import count
from typing import Dict, Iterator

from .protocol import serialize, deserialize, StreamTransformer
from .utils import EndPoint

LOG = logging.getLogger("client")


def _process_client(client: socket.socket, proxy: socket.socket,
                    dirmap: Dict[EndPoint, int],
                    revmap: Dict[int, EndPoint],
                    tags: Iterator[int]) -> None:
    """Transfer UDP message from the client socket to the proxy."""
    with contextlib.suppress(BlockingIOError):
        while True:
            data, endpoint = client.recvfrom(65535, socket.MSG_DONTWAIT)
            if endpoint not in dirmap:
                tag = next(tags)
                dirmap[endpoint] = tag
                revmap[tag] = endpoint
                LOG.info("new client endpoint: %s = [%s]", endpoint, tag)

            tag = dirmap[endpoint]
            message = serialize((tag, data))
            proxy.sendall(message)


def _process_proxy(client: socket.socket, proxy: socket.socket,
                   revmap: Dict[int, EndPoint],
                   deserializer: StreamTransformer) -> None:
    """Process flow from the proxy."""
    with contextlib.suppress(BlockingIOError):
        while True:
            chunk = proxy.recv(4096, socket.MSG_DONTWAIT)
            assert chunk, "the TCP connection is closed, may be proxy failure"

            msgs = deserializer.send(chunk)
            for tag, dgram in msgs:
                assert tag in revmap, "proxy and client are not synchronized"
                client.sendto(dgram, revmap[tag])


def _client_loop(client: socket.socket, proxy: socket.socket) -> None:
    """Run client loop forever."""
    # prepare mappings for client endpoints
    tags = count()
    dirmap: Dict[EndPoint, int] = {}
    revmap: Dict[int, EndPoint] = {}

    # prepare sockets for a selector
    sel = selectors.DefaultSelector()
    sel.register(client, selectors.EVENT_READ)
    sel.register(proxy, selectors.EVENT_READ)

    # prepare stream transformer for TCP
    deserializer = deserialize()
    deserializer.send(None)

    with contextlib.suppress(KeyboardInterrupt):
        while True:
            events = sel.select()
            for key, _ in events:
                if key.fileobj is client:
                    _process_client(client, proxy, dirmap, revmap, tags)
                if key.fileobj is proxy:
                    _process_proxy(client, proxy, revmap, deserializer)

    LOG.info("\nInterrupted, closing")


def start_uott_client(local_udp: EndPoint, remote_tcp: EndPoint) -> None:
    """Start UOTT client."""
    LOG.info("starting UOTT client: UDP:%s -> TCP:%s", local_udp, remote_tcp)

    # keep all the sockets in the ExitStack
    with contextlib.ExitStack() as stack:
        LOG.info("connecting to the remote TCP endpoint")
        proxy = stack.enter_context(socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM))
        proxy.connect(remote_tcp)

        LOG.info("creating the local UDP endpoint")
        client = stack.enter_context(socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM))
        client.bind(local_udp)

        LOG.info("starting client loop")
        _client_loop(client, proxy)
