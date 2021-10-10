"""protocol - base definitions for uott protocol."""

from dataclasses import dataclass
from typing import Generator, List, Tuple

from .utils import split_at

_MAGIC = b"UOTT"
_TAG_BYTES = 2
_LEN_BYTES = 2
_BYTEORDER = "little"

UOTTTag = int
UOTTData = bytes
UOTTMsg = Tuple[UOTTTag, UOTTData]
StreamTransformer = Generator[bytes, List[UOTTMsg], None]


@dataclass
class _UOTTFrags:
    """UOTT message fragments."""

    magic: bytes
    tag: bytes
    len: bytes
    data: bytes

    def clear(self):
        """Clear all collected fragments."""
        self.magic = b""
        self.tag = b""
        self.len = b""
        self.data = b""


def _deserialize_chunk(chunk: bytes, frags: _UOTTFrags) -> List[UOTTMsg]:
    """Start the loop over given chunk.

    Consume the given chunk and return the collected messages. All fragments
    are kept in `frags`.
    """
    ready = []
    while chunk:
        if len(frags.magic) < len(_MAGIC):
            delta = len(_MAGIC) - len(frags.magic)
            appendix, chunk = split_at(chunk, delta)
            frags.magic += appendix

            # check magic immediately to detect stream corruption early
            assert _MAGIC.startswith(frags.magic), f"corrupted: {frags.magic}"

        if len(frags.tag) < _TAG_BYTES:
            delta = _TAG_BYTES - len(frags.tag)
            appendix, chunk = split_at(chunk, delta)
            frags.tag += appendix

        if len(frags.len) < _LEN_BYTES:
            delta = _LEN_BYTES - len(frags.len)
            appendix, chunk = split_at(chunk, delta)
            frags.len += appendix

        # do not pass to the `data` step when `len` fragment is not complete
        if len(frags.len) < _LEN_BYTES:
            continue

        dlen = int.from_bytes(frags.len, _BYTEORDER)
        if len(frags.data) < dlen:
            delta = dlen - len(frags.data)
            appendix, chunk = split_at(chunk, delta)
            frags.data += appendix

        # check whether the message is completed
        if len(frags.data) == dlen:
            message = (int.from_bytes(frags.tag, _BYTEORDER), frags.data)
            ready.append(message)
            frags.clear()

    return ready


def deserialize() -> StreamTransformer:
    """Deserialize UOTT message from bytestream using coroutine."""
    # accumulate ready messages from the stream
    msgs = []

    # keep already collected message fragments
    frags = _UOTTFrags(b"", b"", b"", b"")

    while True:
        chunk = yield msgs
        msgs = _deserialize_chunk(chunk, frags)


def serialize(uott: UOTTMsg) -> bytes:
    """Convert UOTT message to bytes."""
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
