"""Wire protocol constants. Messages are dicts with a "type" key.

Both sides import the same names so typos surface as ImportError instead of
silent string mismatches.

Threat model: the host is implicitly trusted by every joining client (you
chose to connect). Clients are NOT trusted by the host — never deserialise
a client message into anything that runs code. Inputs are dict-of-primitives
only and validated server-side."""
DEFAULT_PORT = 50515
PROTOCOL_VERSION = 1

# --- C → S ---
C_HELLO = "hello"           # {type, name, version}
C_INPUT = "input"           # {type, frame, keys: [int], mouse_pos: [x, y], buttons: [bool, bool, bool]}
C_CHAT = "chat"             # {type, text}
C_READY = "ready"           # {type, ready: bool}
C_VOTE = "vote"             # {type, map: str}
C_GOODBYE = "goodbye"

# --- S → C ---
S_WELCOME = "welcome"       # {type, player_id, version}
S_REJECT = "reject"         # {type, reason}
S_LOBBY = "lobby"           # {type, players: [{id, name, ready}], map_name, hosting_name, maps, votes}
S_CHAT = "chat_msg"         # {type, from_name, text}
S_START_GAME = "start_game" # {type, map_name, grid, background, door_costs, wall_buy_weapons, perk_machine_perks}
S_SNAPSHOT = "snapshot"     # {type, tick, players, zombies, bullets, pickups, grenades, blood, muzzle, floats, interactables, round, round_text_countdown, kill_count, damage_flash_alpha, points_multiplier}
S_EVENT = "event"           # {type, event, data}  (e.g. shoot/reload sound triggers)
S_GAME_OVER = "game_over"   # {type, final_round, final_kills}
S_GOODBYE = "goodbye"
