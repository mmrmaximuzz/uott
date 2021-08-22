"""dispatch - module for dispatching data between sockets."""

import socket


def loop(udp: socket.socket, tcp: socket.socket) -> None:
    """Launch socket loop with the sockets given."""
