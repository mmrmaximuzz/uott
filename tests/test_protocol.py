"""Testing suite for uott protocol module."""

from typing import List

import pytest

from uott import protocol


def test_serialize_empty():
    """UDP datagrams can be zero-sized."""
    tag, dgram = 100, b""
    actual = protocol.serialize((tag, dgram))
    expect = b"".join([
        protocol._MAGIC,
        (100).to_bytes(protocol._TAG_BYTES, protocol._BYTEORDER),
        (0).to_bytes(protocol._LEN_BYTES, protocol._BYTEORDER),
    ])
    assert actual == expect


def test_serialize_normal():
    """Test ordinary datagrams."""
    tag, dgram = 200, b"0123456789abcdef"
    actual = protocol.serialize((tag, dgram))
    expect = b"".join([
        protocol._MAGIC,
        (200).to_bytes(protocol._TAG_BYTES, protocol._BYTEORDER),
        (16).to_bytes(protocol._LEN_BYTES, protocol._BYTEORDER),
        dgram,
    ])
    assert actual == expect


def test_serialize_oversized_data():
    """Should raise assertion on oversized datagrams."""
    with pytest.raises(AssertionError):
        protocol.serialize((0, b"0" * 65536))


def test_serialize_tag_overflow():
    """Should raise assertion on tag overflow."""
    with pytest.raises(AssertionError):
        protocol.serialize((65536, b""))


def _deserialize_oneshot(bs: bytes) -> List[protocol.UOTTMsg]:
    deserializer = protocol.deserialize()
    deserializer.send(None)
    return deserializer.send(bs)


def test_deserialize_bad_magic():
    """Should raise assertion when magic does not match."""
    with pytest.raises(AssertionError):
        _deserialize_oneshot(b"!")

    with pytest.raises(AssertionError):
        _deserialize_oneshot(b"U!")

    with pytest.raises(AssertionError):
        _deserialize_oneshot(b"UO!")

    with pytest.raises(AssertionError):
        _deserialize_oneshot(b"UOT!")

    assert _deserialize_oneshot(b"UOTT") == []


def test_desertialize_empty():
    """Convert empty UDP datagrams back from TCP."""
    chunk = b"UOTT\x30\x01\x00\x00"
    assert _deserialize_oneshot(chunk) == [(0x0130, b"")]


def test_deserialize_short():
    """Should return empty list when the message is not completed."""
    msg = b"UOTT\xfe\xef\x01\x00"

    deserializer = protocol.deserialize()
    deserializer.send(None)
    for byte in msg:
        assert deserializer.send(byte.to_bytes(1, "little")) == []

    assert deserializer.send(b"\xfe") == [(0xEFFE, b"\xfe")]


def test_deserialize_multiple():
    """Should return all messages from the one chunk."""
    chunk1 = b"UOTT\x01\x10\x01\x00\xA1"
    chunk2 = b"UOTT\x02\x20\x02\x00\xB2\xB2"
    chunk3 = b"UOTT\x03\x30\x03\x00\xC3\xC3\xC3"

    chunk = chunk1 + chunk2 + chunk3

    msg1, msg2, msg3 = _deserialize_oneshot(chunk)
    assert msg1 == (0x1001, b"\xA1")
    assert msg2 == (0x2002, b"\xB2\xB2")
    assert msg3 == (0x3003, b"\xC3\xC3\xC3")
