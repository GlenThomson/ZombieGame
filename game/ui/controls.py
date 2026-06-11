"""Single source of truth for the controls list. Shown on the main-menu
Controls screen and the in-game pause overlay — update HERE when a
keybinding changes so the two never drift apart again."""

CONTROLS: list[tuple[str, str]] = [
    ("W A S D",      "move"),
    ("Mouse",        "aim"),
    ("Left click",   "shoot"),
    ("R",            "reload"),
    ("F",            "interact (doors / buys / box / power)"),
    ("F (hold)",     "revive a downed teammate"),
    ("G",            "throw grenade"),
    ("T",            "throw monkey bomb (if you have one)"),
    ("1 / 2 / 3",    "switch weapon slot"),
    ("Tab (hold)",   "scoreboard"),
    ("P",            "pause (single-player only)"),
    ("ESC",          "leave game / back to menu"),
]
