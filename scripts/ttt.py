#!/usr/bin/env python3
"""Profile tic-tac-toe, driven by GitHub issues.

Protocol: an issue titled exactly `ttt: move A1` (coordinate case-insensitive)
plays that square for whoever's turn it is. Anything else is ignored, except
`ttt:`-prefixed titles, which get a short usage reply. State lives in
ttt/state.json; the board is rendered into README.md between the
<!-- TTT:START --> and <!-- TTT:END --> markers. Every handled issue gets a
reply in ttt/reply.md for the workflow to post before closing the issue.

Standard library only.
"""

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "ttt" / "state.json"
README_PATH = ROOT / "README.md"
REPLY_PATH = ROOT / "ttt" / "reply.md"

MOVE_RE = re.compile(r"^ttt: move ([A-Ca-c][1-3])$")
NEW_ISSUE = "https://github.com/Sun-Wukhan/Sun-Wukhan/issues/new?title="
MARKS = {"X": "❌", "O": "⭕"}
LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def load_state():
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def coord_to_index(coord):
    col = "ABC".index(coord[0])
    row = int(coord[1]) - 1
    return row * 3 + col


def index_to_coord(idx):
    return "ABC"[idx % 3] + str(idx // 3 + 1)


def winner(board):
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def render_section(state):
    board = state["board"]
    out = ["| | A | B | C |", "| --- | --- | --- | --- |"]
    for row in range(3):
        cells = []
        for col in range(3):
            idx = row * 3 + col
            coord = index_to_coord(idx)
            mark = board[idx]
            if mark:
                cells.append(MARKS[mark])
            else:
                url = NEW_ISSUE + quote(f"ttt: move {coord}", safe="")
                cells.append(f"[⬜]({url})")
        out.append(f"| **{row + 1}** | " + " | ".join(cells) + " |")
    out.append("")
    turn = state["turn"]
    out.append(f"**Turn:** {MARKS[turn]} ({turn}) to move · **Game #{state['game_number']}**")
    last = state["last_move"] or "none yet"
    out.append(f"**Last move:** {last}")
    out.append("")
    wins = state["wins"]
    if wins:
        top = sorted(wins.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        board_lines = [f"{i}. @{user}: {n}" for i, (user, n) in enumerate(top, 1)]
        out.append("**Scoreboard (wins):** " + " · ".join(board_lines))
    else:
        out.append("**Scoreboard (wins):** no wins yet, be the first.")
    out.append(f"**Draws:** {state['draws']}")
    return "\n".join(out)


def update_readme(state):
    text = README_PATH.read_text(encoding="utf-8")
    start = text.index("<!-- TTT:START -->") + len("<!-- TTT:START -->")
    end = text.index("<!-- TTT:END -->")
    new = text[:start] + "\n\n" + render_section(state) + "\n\n" + text[end:]
    README_PATH.write_text(new, encoding="utf-8")


def write_reply(text):
    REPLY_PATH.write_text(text + "\n", encoding="utf-8")


def reset_board(state):
    state["board"] = [""] * 9
    state["turn"] = "X"
    state["game_number"] += 1


def main():
    title = os.environ.get("ISSUE_TITLE", "")
    user = os.environ.get("ISSUE_USER", "someone")

    match = MOVE_RE.match(title.strip())
    if not match:
        if title.strip().lower().startswith("ttt:"):
            write_reply(
                "That title does not match the game protocol. To play, open an "
                "issue titled exactly `ttt: move A1` (column A to C, row 1 to 3), "
                "or click an empty square on the profile board."
            )
        # Not a game move: never touch state or the README.
        return 0

    coord = match.group(1).upper()
    state = load_state()
    idx = coord_to_index(coord)

    if state["board"][idx]:
        write_reply(
            f"Square {coord} is already taken by {MARKS[state['board'][idx]]}. "
            "No move was made; pick an empty square from the board on the profile."
        )
        return 0

    mark = state["turn"]
    state["board"][idx] = mark
    state["last_move"] = f"@{user} took {coord} as {mark}"
    reply = f"Move accepted: @{user} took {coord} as {mark} ({MARKS[mark]})."

    win = winner(state["board"])
    if win:
        state["wins"][user] = state["wins"].get(user, 0) + 1
        reply += (
            f"\n\n🏆 @{user} wins the game for {win}! "
            f"That is win #{state['wins'][user]} for @{user}. "
            "The board has been reset for a new game; X moves first."
        )
        reset_board(state)
    elif all(state["board"]):
        state["draws"] += 1
        reply += (
            "\n\n🤝 It is a draw. The board has been reset for a new game; "
            "X moves first."
        )
        reset_board(state)
    else:
        state["turn"] = "O" if mark == "X" else "X"
        reply += f" Next up: {state['turn']} to move."

    save_state(state)
    update_readme(state)
    write_reply(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
