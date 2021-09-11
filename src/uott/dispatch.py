"""dispatch - module for dispatching data between sockets."""

import contextlib
import selectors
import socket

from .protocol import udp_dgram_to_tcp_msg, tcp_msg_to_udp_dgram
from .protocol import MAGIC, LEN_BYTES, BYTEORDER


MAX_UDP_DGRAM_SIZE: int = 65535


def send_to_tunnel(udp: socket.socket, tcp: socket.socket) -> None:
    """Take a datagram from the UDP socket, pack and send to the TCP tunnel."""
    # UDP socket is message-oriented, get full datagram in one recv call
    dgram = udp.recv(MAX_UDP_DGRAM_SIZE)

    # pack datagram to UOTT message and send to TCP stream
    uott_msg = udp_dgram_to_tcp_msg(dgram)
    tcp.sendall(uott_msg)


def recv_from_tunnel(tcp: socket.socket, udp: socket.socket) -> None:
    """Take a datagram from the UDP socket, pack and send to the TCP tunnel."""
    # assemble UOTT message from TCP stream
    magic = tcp.recv(len(MAGIC), socket.MSG_WAITALL)
    msglen = tcp.recv(LEN_BYTES, socket.MSG_WAITALL)
    msg = tcp.recv(int.from_bytes(msglen, BYTEORDER), socket.MSG_WAITALL)
    uott_msg = magic + msglen + msg

    # unpack UDP datagram and send to UDP socket
    dgram = tcp_msg_to_udp_dgram(uott_msg)
    udp.send(dgram)


def loop(udp: socket.socket, tcp: socket.socket) -> None:
    """Launch socket loop with the sockets given."""
    sel = selectors.DefaultSelector()
    sel.register(udp, selectors.EVENT_READ)
    sel.register(tcp, selectors.EVENT_READ)

    # start event loop, exit by ctrl+c
    with contextlib.suppress(KeyboardInterrupt):
        while True:
            events = sel.select()
            for key, _ in events:
                if key.fileobj is udp:
                    send_to_tunnel(udp, tcp)
                if key.fileobj is tcp:
                    recv_from_tunnel(tcp, udp)

    print("Interrupted")
