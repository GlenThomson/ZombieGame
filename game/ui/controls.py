"""Single source of truth for the controls list. Shown on the main-menu
Controls screen and the in-game pause overlay — update HERE when a
keybinding changes so the two never drift apart again."""

CONTROLS: list[tuple[str, str]] = [
    ("W A S D",      "move"),
    ("Shift",        "sprint"),
    ("Mouse",        "aim"),
    ("Left click",   "shoot"),
    ("Wheel",        "switch weapon"),
    ("R",            "reload"),
    ("F",            "interact (doors / buys / box / power)"),
    ("F (hold)",     "revive a downed teammate"),
    ("G",            "throw grenade (at your cursor)"),
    ("T",            "throw monkey bomb"),
    ("1 / 2 / 3",    "weapon slots"),
    ("Tab (hold)",   "scoreboard"),
    ("M",            "mute / unmute"),
    ("P / ESC",      "pause menu (SP) - double-ESC leaves MP"),
    ("F11",          "fullscreen on / off"),
]
