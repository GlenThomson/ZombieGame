"""Network client (the joining player).

Background thread reads incoming messages, drops them into a thread-safe
queue. Main thread drains the queue once per frame and reacts. Sending is
just blocking sendall (one-way, low-volume from client to host)."""
from __future__ import annotations

import socket
import threading
from queue import Queue, Empty
from typing import Optional

from game.net import protocol
from game.net.framing import FrameReader, encode, send_message


class NetClient:
    def __init__(self):
        self._sock: Optional[socket.socket] = None
        self._reader = FrameReader()
        self._reader_thread: Optional[threading.Thread] = None
        self._send_lock = threading.Lock()
        self.incoming: "Queue[dict]" = Queue()
        self.connected = False
        self.last_error: str | None = None

    def connect(self, host: str, port: int = protocol.DEFAULT_PORT, name: str = "Player",
                timeout: float = 4.0) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
        except (OSError, socket.timeout) as e:
            self.last_error = str(e)
            return False
        sock.settimeout(None)
        # Match the host: disable Nagle's so per-frame input packets don't
        # get held in the OS buffer. Without this, holding W could feel
        # noticeably laggy on Windows.
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        self._sock = sock
        self.connected = True
        self.send({"type": protocol.C_HELLO, "name": name, "version": protocol.PROTOCOL_VERSION})
        self._reader_thread = threading.Thread(
            target=self._read_loop, daemon=True, name="net-client-reader",
        )
        self._reader_thread.start()
        return True

    def _read_loop(self):
        try:
            while self.connected and self._sock is not None:
                chunk = self._sock.recv(8192)
                if not chunk:
                    break
                self._reader.feed(chunk)
                for msg in self._reader.messages():
                    self.incoming.put(msg)
        except (ConnectionError, OSError) as e:
            self.last_error = str(e)
        finally:
            self.connected = False

    def send(self, message: dict):
        if not self.connected or self._sock is None:
            return
        try:
            with self._send_lock:
                self._sock.sendall(encode(message))
        except (ConnectionError, OSError) as e:
            self.last_error = str(e)
            self.connected = False

    def drain_incoming(self) -> list[dict]:
        out = []
        while True:
            try:
                out.append(self.incoming.get_nowait())
            except Empty:
                return out

    def close(self):
        if self.connected:
            try:
                self.send({"type": protocol.C_GOODBYE})
            except Exception:
                pass
        self.connected = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
