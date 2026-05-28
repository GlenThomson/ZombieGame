"""Authoritative host server.

Runs in a background thread, accepting client connections, reading their
inputs into a per-client `latest_input` dict, and exposing a `broadcast()`
method the main game loop calls each frame to push the latest snapshot.

The game loop owns the timeline; this class just ferries bytes."""
from __future__ import annotations

import socket
import threading
import time
from typing import Optional

from game.net import protocol
from game.net.framing import FrameReader, encode, send_message


class _ClientHandle:
    """One connected client from the host's point of view."""

    def __init__(self, sock: socket.socket, addr, player_id: int):
        self.sock = sock
        self.addr = addr
        self.player_id = player_id
        self.name = f"Player{player_id + 1}"
        self.latest_input: dict = _empty_input()
        self.connected = True
        self.send_lock = threading.Lock()
        self._reader = FrameReader()

    def read_loop(self, on_disconnect):
        try:
            while self.connected:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                self._reader.feed(chunk)
                for msg in self._reader.messages():
                    self._handle(msg)
        except (ConnectionError, OSError):
            pass
        finally:
            self.connected = False
            try:
                self.sock.close()
            except OSError:
                pass
            on_disconnect(self)

    def _handle(self, msg: dict):
        kind = msg.get("type")
        if kind == protocol.C_HELLO:
            name = str(msg.get("name", self.name))[:24]
            self.name = name or self.name
        elif kind == protocol.C_INPUT:
            # Defensive: keep only the keys we expect, coerce types.
            self.latest_input = {
                "keys": tuple(int(k) for k in msg.get("keys", ())),
                "mouse_pos": tuple(int(v) for v in msg.get("mouse_pos", (0, 0))[:2]),
                "buttons": tuple(bool(b) for b in msg.get("buttons", (False, False, False))[:3]),
                "events": tuple(msg.get("events", ())),  # discrete keypresses (e.g. weapon switch)
                "frame": int(msg.get("frame", 0)),
            }
        elif kind == protocol.C_GOODBYE:
            self.connected = False

    def send(self, message: dict):
        if not self.connected:
            return
        try:
            with self.send_lock:
                self.sock.sendall(encode(message))
        except (ConnectionError, OSError):
            self.connected = False


def _empty_input() -> dict:
    return {
        "keys": (),
        "mouse_pos": (0, 0),
        "buttons": (False, False, False),
        "events": (),
        "frame": 0,
    }


class HostServer:
    def __init__(self, port: int = protocol.DEFAULT_PORT, max_clients: int = 3):
        self.port = port
        self.max_clients = max_clients
        self._server_sock: Optional[socket.socket] = None
        self._accept_thread: Optional[threading.Thread] = None
        self.clients: list[_ClientHandle] = []
        self._clients_lock = threading.Lock()
        # Reuse the lowest unused pid >= 1 (host is always 0). Stops pids
        # drifting upward after disconnect/reconnect cycles, which would
        # cause player_id mismatches downstream.
        self._running = False
        self.on_client_joined = lambda c: None
        self.on_client_left = lambda c: None

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.port))
        sock.listen(self.max_clients)
        sock.settimeout(0.5)
        self._server_sock = sock
        self._running = True
        self._accept_thread = threading.Thread(
            target=self._accept_loop, daemon=True, name="net-host-accept",
        )
        self._accept_thread.start()

    def _accept_loop(self):
        while self._running:
            try:
                sock, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            # Disable Nagle's algorithm so small per-frame snapshots ship
            # immediately instead of being held in the OS buffer up to
            # 200ms — major cause of "lag spikes" on LAN/WAN play.
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass
            with self._clients_lock:
                if len(self.clients) >= self.max_clients:
                    try:
                        send_message(sock, {
                            "type": protocol.S_REJECT, "reason": "lobby full",
                        })
                    finally:
                        sock.close()
                    continue
                pid = self._allocate_pid_locked()
                handle = _ClientHandle(sock, addr, pid)
                self.clients.append(handle)
            handle.send({
                "type": protocol.S_WELCOME,
                "player_id": pid,
                "version": protocol.PROTOCOL_VERSION,
            })
            t = threading.Thread(
                target=handle.read_loop, args=(self._on_client_disconnect,),
                daemon=True, name=f"net-host-client-{pid}",
            )
            t.start()
            self.on_client_joined(handle)

    def _allocate_pid_locked(self) -> int:
        """Return the smallest pid >= 1 not currently in use by a connected
        client. Caller must hold self._clients_lock."""
        used = {c.player_id for c in self.clients}
        pid = 1
        while pid in used:
            pid += 1
        return pid

    def _on_client_disconnect(self, handle: _ClientHandle):
        with self._clients_lock:
            if handle in self.clients:
                self.clients.remove(handle)
        self.on_client_left(handle)

    def connected_clients(self) -> list[_ClientHandle]:
        with self._clients_lock:
            return list(self.clients)

    def broadcast(self, message: dict):
        # Encode once, send to each.
        try:
            payload = encode(message)
        except Exception:
            return
        for client in self.connected_clients():
            if not client.connected:
                continue
            try:
                with client.send_lock:
                    client.sock.sendall(payload)
            except (ConnectionError, OSError):
                client.connected = False

    def get_input(self, player_id: int) -> dict:
        for client in self.connected_clients():
            if client.player_id == player_id:
                return client.latest_input
        return _empty_input()

    def shutdown(self):
        self._running = False
        with self._clients_lock:
            for client in self.clients:
                client.connected = False
                try:
                    client.sock.close()
                except OSError:
                    pass
            self.clients.clear()
        if self._server_sock is not None:
            try:
                self._server_sock.close()
            except OSError:
                pass
        # Give the accept thread a beat to notice (it polls every 0.5s).
        time.sleep(0.05)
