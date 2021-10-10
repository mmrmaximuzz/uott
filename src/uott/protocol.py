"""protocol - base definitions for uott protocol."""

from typing import Generator, Optional, Tuple

from .utils import split_at

_MAGIC = b"UOTT"
_TAG_BYTES = 2
_LEN_BYTES = 2
_BYTEORDER = "little"

UOTTTag = int
UOTTData = bytes
UOTTMsg = Tuple[UOTTTag, UOTTData]
StreamTransformer = Generator[bytes, Optional[UOTTMsg], None]


def udp_dgram_to_tcp_msg(uott: UOTTMsg) -> bytes:
    """Convert UDP datagram to UOTT TCP message with given tag."""
    tag, data = uott

    dlen = len(data)
    assert dlen <= 0xFFFF, f"oversized UDP datagram: {dlen} B"
    assert tag <= 0xFFFF, f"tag ID overflow: {tag}"

    parts = [
        _MAGIC,
        tag.to_bytes(_TAG_BYTES, _BYTEORDER),
        dlen.to_bytes(_LEN_BYTES, _BYTEORDER),
        data,
    ]
    return b"".join(parts)


def tcp_msg_to_udp_dgram_transformer() -> StreamTransformer:
    """Convert UOTT TCP message to UDP datagram in a coroutine."""
