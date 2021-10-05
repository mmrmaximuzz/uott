"""dispatch - module for dispatching data between sockets."""

import contextlib
import selectors
import socket
from typing import Generator, Optional

from .protocol import udp_dgram_to_tcp_msg, tcp_msg_to_udp_dgram


MAX_UDP_DGRAM_SIZE: int = 65535
StreamTransformer = Generator[bytes, Optional[bytes], None]


def stream_transformer() -> StreamTransformer:
    """Collect fragments from TCP stream and split them to UOTT messages."""
    chunk = b""
    while True:
        res = tcp_msg_to_udp_dgram(chunk)
        if res:
            dgram, chunk = res
        else:
            dgram = None

        chunk += yield dgram


def recv_from_tunnel(tcp: socket.socket,
                     udp: socket.socket,
                     sttrans: StreamTransformer) -> None:
    """Take a chunk from TCP stream and collect."""
    with contextlib.suppress(BlockingIOError):
        while True:
            data = tcp.recv(1024, socket.MSG_DONTWAIT)
            dgram = sttrans.send(data)
            if dgram is not None:
                udp.send(dgram)


def send_to_tunnel(udp: socket.socket, tcp: socket.socket) -> None:
    """Take a datagram from the UDP socket, pack and send to the TCP tunnel."""
    # UDP socket is message-oriented, get full datagram in one recv call
    dgram = udp.recv(MAX_UDP_DGRAM_SIZE)

    # pack datagram to UOTT message and send to TCP stream
    uott_msg = udp_dgram_to_tcp_msg(dgram)
    tcp.sendall(uott_msg)


def loop(udp: socket.socket, tcp: socket.socket) -> None:
    """Launch socket loop with the sockets given."""
    # prepare sockets for a selector
    sel = selectors.DefaultSelector()
    sel.register(udp, selectors.EVENT_READ)
    sel.register(tcp, selectors.EVENT_READ)

    # prepare stream transformer for TCP
    sttrans = stream_transformer()
    sttrans.send(None)

    # start event loop, exit by ctrl+c
    with contextlib.suppress(KeyboardInterrupt):
        while True:
            events = sel.select()
            for key, _ in events:
                if key.fileobj is udp:
                    send_to_tunnel(udp, tcp)
                if key.fileobj is tcp:
                    recv_from_tunnel(tcp, udp, sttrans)

    print("Interrupted")
