"""Testing suite for uott protocol module."""

import pytest

from uott import protocol


def test_udp_to_tcp_empty():
    """UDP datagrams can be zero-sized."""
    dgram = b""
    msg = protocol.udp_dgram_to_tcp_msg(dgram)
    assert msg == protocol.MAGIC + (0).to_bytes(2, "little")


def test_udp_to_tcp_normal():
    """Test ordinary datagrams."""
    dgram = b"0123456789abcdef"
    msg = protocol.udp_dgram_to_tcp_msg(dgram)
    assert msg == protocol.MAGIC + (16).to_bytes(2, "little") + dgram


def test_udp_to_tcp_oversized():
    """Should raise assertion on oversized datagrams."""
    with pytest.raises(AssertionError):
        dgram = b"0" * 65536
        protocol.udp_dgram_to_tcp_msg(dgram)


def test_tcp_to_udp_empty():
    """Convert empty UDP datagrams back from TCP."""
    msg = b"UOTT\x00\x00"
    assert protocol.tcp_msg_to_udp_dgram(msg) == b""


def test_tcp_to_udp_bad_magic():
    """Should raise assertion when magic does not match."""
    with pytest.raises(AssertionError):
        msg = b"HAHA\x00\x00"
        protocol.tcp_msg_to_udp_dgram(msg)


def test_tcp_to_udp_too_short():
    """Should raise assertion when the message is too short."""
    with pytest.raises(AssertionError):
        msg = b"UOTT\x00"
        protocol.tcp_msg_to_udp_dgram(msg)


def test_tcp_to_udp_dgram_len_short():
    """Should raise assertion when the dgram len lesser than msg field."""
    with pytest.raises(AssertionError):
        msg = b"UOTT\x03\x00\xff\xff"
        protocol.tcp_msg_to_udp_dgram(msg)
