"""Testing suite for uott protocol module."""

import pytest

from uott import protocol


def test_udp_to_tcp_empty():
    """UDP datagrams can be zero-sized."""
    udp_dgram = b""
    uott_msg = protocol.udp_dgram_to_tcp_msg(udp_dgram)
    assert uott_msg == protocol.MAGIC + (0).to_bytes(2, "little")


def test_udp_to_tcp_normal():
    """Test ordinary datagrams."""
    udp_dgram = b"0123456789abcdef"
    uott_msg = protocol.udp_dgram_to_tcp_msg(udp_dgram)
    assert uott_msg == protocol.MAGIC + (16).to_bytes(2, "little") + udp_dgram


def test_udp_to_tcp_oversized():
    """Should raise assertion on oversized datagrams."""
    with pytest.raises(AssertionError):
        udp_dgram = b"0" * 65536
        protocol.udp_dgram_to_tcp_msg(udp_dgram)


def test_tcp_to_udp_empty():
    """Convert empty UDP datagrams back from TCP."""
    uott_msg = b"UOTT\x00\x00"
    assert protocol.tcp_msg_to_udp_dgram(uott_msg) == b""


def test_tcp_to_udp_bad_magic():
    """Should raise assertion when magic does not match."""
    with pytest.raises(AssertionError):
        uott_msg = b"HAHA\x00\x00"
        protocol.tcp_msg_to_udp_dgram(uott_msg)
