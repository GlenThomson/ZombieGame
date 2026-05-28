"""LAN game discovery.

Host opens a UDP socket and broadcasts a tiny announcement packet to the
local network every ANNOUNCE_INTERVAL seconds. Joining clients open a
listener that records every announcement they see, expiring entries that
haven't been heard from recently. The join screen renders the list so
players can click instead of typing an IP.

UDP-only — TCP is still used for the actual game session (port stays in
settings.DEFAULT_HOST_PORT). Discovery uses DEFAULT_HOST_PORT + 1 so it
can't collide with the gameplay socket.
"""
from __future__ import annotations

import pickle
import socket
import threading
import time

from settings import DEFAULT_HOST_PORT


DISCOVERY_PORT = DEFAULT_HOST_PORT + 1     # 50516 by default
ANNOUNCE_INTERVAL = 1.0                    # seconds between broadcasts
ENTRY_TTL = 4.0                            # forget hosts not heard from in N seconds
MAGIC = b"ZOMBIESGAME-LAN-V1"              # filters out random UDP traffic


def _build_announcement(host_name: str, game_port: int, map_name: str,
                        player_count: int, max_players: int, in_game: bool) -> bytes:
    payload = {
        "magic": MAGIC,
        "host_name": host_name,
        "port": game_port,
        "map_name": map_name,
        "players": int(player_count),
        "max_players": int(max_players),
        "in_game": bool(in_game),
    }
    return pickle.dumps(payload)


def _parse_announcement(data: bytes) -> dict | None:
    try:
        obj = pickle.loads(data)
    except (pickle.UnpicklingError, EOFError, ValueError):
        return None
    if not isinstance(obj, dict) or obj.get("magic") != MAGIC:
        return None
    return obj


# ---------------- host side ----------------

class DiscoveryAnnouncer:
    """Periodically broadcasts a UDP packet so listening clients can find us
    on the LAN. Cheap — one ~120-byte packet per second."""

    def __init__(self, host_name: str, game_port: int = DEFAULT_HOST_PORT,
                 discovery_port: int = DISCOVERY_PORT):
        self.host_name = host_name
        self.game_port = game_port
        self.discovery_port = discovery_port
        self.map_name = ""
        self.player_count = 1
        self.max_players = 4
        self.in_game = False
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self):
        if self._running:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock = sock
        except OSError:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="net-lan-announce",
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def update(self, *, map_name: str | None = None,
               player_count: int | None = None,
               in_game: bool | None = None):
        if map_name is not None:
            self.map_name = map_name
        if player_count is not None:
            self.player_count = player_count
        if in_game is not None:
            self.in_game = in_game

    def _loop(self):
        while self._running and self._sock is not None:
            try:
                data = _build_announcement(
                    self.host_name, self.game_port, self.map_name,
                    self.player_count, self.max_players, self.in_game,
                )
                # 255.255.255.255 reaches every host on the local subnet.
                # Some networks block this; we don't care if it fails.
                self._sock.sendto(data, ("255.255.255.255", self.discovery_port))
            except OSError:
                pass
            time.sleep(ANNOUNCE_INTERVAL)


# ---------------- client side ----------------

class DiscoveryListener:
    """Background thread that fills self._entries with whatever LAN hosts
    are announcing themselves. `entries()` returns a fresh snapshot list
    sorted by host_name with stale rows expired."""

    def __init__(self, discovery_port: int = DISCOVERY_PORT):
        self.discovery_port = discovery_port
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        # Keyed by (ip, port) so two hosts on the same IP can't collide.
        self._entries: dict[tuple[str, int], dict] = {}

    def start(self):
        if self._running:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind on all interfaces so we hear broadcasts.
            sock.bind(("", self.discovery_port))
            sock.settimeout(0.5)
            self._sock = sock
        except OSError:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="net-lan-listen",
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def entries(self) -> list[dict]:
        """Snapshot of currently-visible hosts. Drops entries we haven't
        heard from in ENTRY_TTL seconds so a host that stopped announcing
        disappears from the list."""
        now = time.monotonic()
        out: list[dict] = []
        with self._lock:
            stale = [k for k, v in self._entries.items() if now - v["last_seen"] > ENTRY_TTL]
            for k in stale:
                del self._entries[k]
            for (ip, port), info in self._entries.items():
                row = dict(info["payload"])
                row["ip"] = ip
                row["port"] = port
                out.append(row)
        out.sort(key=lambda r: (r.get("host_name", ""), r.get("ip", "")))
        return out

    def _loop(self):
        while self._running and self._sock is not None:
            try:
                data, addr = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            payload = _parse_announcement(data)
            if payload is None:
                continue
            ip = addr[0]
            game_port = int(payload.get("port", DEFAULT_HOST_PORT))
            key = (ip, game_port)
            with self._lock:
                self._entries[key] = {
                    "last_seen": time.monotonic(),
                    "payload": payload,
                }
