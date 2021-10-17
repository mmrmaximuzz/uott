"""Integration test for UOTT proxy/client."""

import socket
import threading
import time

from uott.client import start_uott_client
from uott.proxy import start_uott_proxy

LOOPBACK_ADDR = "127.1.2.3"  # use nonstandard loopback addr
UOTT_CLIENT_UDP_EP = (LOOPBACK_ADDR, 50000)
UOTT_PROXY_TCP_EP = (LOOPBACK_ADDR, 50001)


def test_integration_on_loopback() -> None:
    """Run the simple integration test on a loopback device."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as remote, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        # bind UDP endpoints to a dynamic ports
        client.bind((LOOPBACK_ADDR, 0))
        remote.bind((LOOPBACK_ADDR, 0))
        remote_ep = remote.getsockname()

        # run uott threads
        uott_proxy = threading.Thread(target=start_uott_proxy,
                                      args=(UOTT_PROXY_TCP_EP, remote_ep))
        uott_client = threading.Thread(target=start_uott_client,
                                       args=(UOTT_CLIENT_UDP_EP,
                                             UOTT_PROXY_TCP_EP))

        # There is no way to force thread cancellation in Python. When the test
        # is completed, we will block forever `join`ing these uott threads, so
        # just make them daemons to allow the main thread to finish.
        uott_proxy.daemon = True
        uott_client.daemon = True

        # wait for the proxy to create the TCP endpoint
        uott_proxy.start()
        time.sleep(0.2)
        uott_client.start()
        time.sleep(0.2)

        # ping `remote` from the `client`
        client.sendto(b"loopbackrequest", UOTT_CLIENT_UDP_EP)
        time.sleep(0.1)  # TODO: use recv with timeout
        msg, addr = remote.recvfrom(100, socket.MSG_DONTWAIT)
        assert msg == b"loopbackrequest"

        remote.sendto(b"loopbackreply", addr)
        time.sleep(0.1)  # TODO: use recv with timeout
        msg, addr = client.recvfrom(100, socket.MSG_DONTWAIT)
        assert msg == b"loopbackreply"
        assert addr == UOTT_CLIENT_UDP_EP
