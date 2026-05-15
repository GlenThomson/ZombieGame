"""TCP message framing.

Each message is a length-prefixed pickled dict:
    [4 bytes big-endian payload length] [payload bytes]

Why pickle? It's stdlib, handles tuples / dataclasses cleanly, and keeps the
host->client snapshot format flexible without serializer schemas. The host
trusts itself and the client trusts the host (the user opted in to that
host's IP). Client → host messages are dict-only and validated, see
host.py for the validation layer."""
import io
import pickle
import socket
import struct


_HEADER = struct.Struct(">I")   # 4-byte unsigned big-endian length
_MAX_MSG = 4 * 1024 * 1024     # 4 MB hard cap, snapshots are far below this


def encode(message: dict) -> bytes:
    payload = pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL)
    if len(payload) > _MAX_MSG:
        raise ValueError(f"message too big: {len(payload)} bytes")
    return _HEADER.pack(len(payload)) + payload


class FrameReader:
    """Stateful reader that buffers partial reads from a non-blocking socket
    and yields complete messages as bytes are consumed."""

    def __init__(self):
        self._buf = bytearray()

    def feed(self, chunk: bytes):
        self._buf.extend(chunk)

    def messages(self):
        """Generator yielding fully-received decoded messages. Stops when the
        buffer no longer holds a complete message; remaining bytes stay
        buffered for the next feed()."""
        while True:
            if len(self._buf) < _HEADER.size:
                return
            (length,) = _HEADER.unpack_from(self._buf, 0)
            if length > _MAX_MSG:
                raise ValueError(f"oversized incoming message: {length}")
            total = _HEADER.size + length
            if len(self._buf) < total:
                return
            payload = bytes(self._buf[_HEADER.size:total])
            del self._buf[:total]
            yield pickle.loads(payload)


def send_message(sock: socket.socket, message: dict) -> None:
    sock.sendall(encode(message))
