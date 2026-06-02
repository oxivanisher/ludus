import copy
from collections import Counter

from ..base import BaseGame, GameMeta

SHIPS = [
    {"type": "battleship", "size": 4, "count": 1},
    {"type": "cruiser",    "size": 3, "count": 2},
    {"type": "destroyer",  "size": 2, "count": 3},
    {"type": "submarine",  "size": 1, "count": 4},
]

_ALL_SHIP_TYPES = {s["type"] for s in SHIPS}
_SHIP_SIZE  = {s["type"]: s["size"]  for s in SHIPS}
_SHIP_COUNT = {s["type"]: s["count"] for s in SHIPS}


def _ship_cells(row: int, col: int, size: int, horizontal: bool) -> list[list[int]]:
    if horizontal:
        return [[row, col + i] for i in range(size)]
    else:
        return [[row + i, col] for i in range(size)]


def _buffer_zone(occupied: set[tuple[int, int]]) -> set[tuple[int, int]]:
    result = set()
    for r, c in occupied:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                result.add((r + dr, c + dc))
    return result


def _all_ship_cells_set(ships: list[dict]) -> set[tuple[int, int]]:
    result = set()
    for ship in ships:
        for cell in ship["cells"]:
            result.add(tuple(cell))
    return result


class Battleship(BaseGame):
    meta = GameMeta(
        slug="battleship",
        name="Battleship",
        description="Place your fleet and sink the enemy ships.",
        min_players=2,
        max_players=2,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "phase": "placement",
            "current_turn": None,
            "ready": [],
            "players": players,
            "boards": {
                players[0]: {"ships": [], "shots": []},
                players[1]: {"ships": [], "shots": []},
            },
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        action_type = action.get("type")

        if action_type == "place":
            if state["phase"] != "placement":
                return False
            if player in state["ready"]:
                return False
            ship_type = action.get("ship")
            if ship_type not in _ALL_SHIP_TYPES:
                return False
            # Check ship quota not exceeded
            placed_of_type = sum(1 for s in state["boards"][player]["ships"] if s["type"] == ship_type)
            if placed_of_type >= _SHIP_COUNT[ship_type]:
                return False
            row = action.get("row")
            col = action.get("col")
            horizontal = action.get("horizontal", True)
            if not isinstance(row, int) or not isinstance(col, int):
                return False
            size = _SHIP_SIZE[ship_type]
            cells = _ship_cells(row, col, size, horizontal)
            # Check bounds
            for r, c in cells:
                if not (0 <= r <= 9 and 0 <= c <= 9):
                    return False
            # Check overlap and adjacency
            occupied = _all_ship_cells_set(state["boards"][player]["ships"])
            for r, c in cells:
                if (r, c) in occupied:
                    return False
            buffer = _buffer_zone(occupied)
            for r, c in cells:
                if (r, c) in buffer:
                    return False
            return True

        elif action_type == "fire":
            if state["phase"] != "battle":
                return False
            if state["current_turn"] != player:
                return False
            row = action.get("row")
            col = action.get("col")
            if not isinstance(row, int) or not isinstance(col, int):
                return False
            if not (0 <= row <= 9 and 0 <= col <= 9):
                return False
            shots = state["boards"][player]["shots"]
            if [row, col] in shots:
                return False
            return True

        elif action_type == "remove":
            if state["phase"] != "placement":
                return False
            if player in state["ready"]:
                return False
            row, col = action.get("row"), action.get("col")
            if not isinstance(row, int) or not isinstance(col, int):
                return False
            return any([row, col] in ship["cells"] for ship in state["boards"][player]["ships"])

        return False

    @staticmethod
    def _players(state: dict) -> list[str]:
        return state.get("players") or list(state["boards"].keys())

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        action_type = action["type"]

        if action_type == "remove":
            row, col = action["row"], action["col"]
            ships = state["boards"][player]["ships"]
            idx = next(i for i, s in enumerate(ships) if [row, col] in s["cells"])
            ships.pop(idx)

        elif action_type == "place":
            ship_type = action["ship"]
            row = action["row"]
            col = action["col"]
            horizontal = action.get("horizontal", True)
            size = _SHIP_SIZE[ship_type]
            cells = _ship_cells(row, col, size, horizontal)
            state["boards"][player]["ships"].append({
                "type": ship_type,
                "cells": cells,
            })
            placed_counts = Counter(s["type"] for s in state["boards"][player]["ships"])
            if all(placed_counts[t] >= _SHIP_COUNT[t] for t in _ALL_SHIP_TYPES):
                state["ready"].append(player)
            # Both players ready → start battle
            if len(state["ready"]) == 2:
                state["phase"] = "battle"
                state["current_turn"] = self._players(state)[0]

        elif action_type == "fire":
            players = self._players(state)
            opponent = players[1] if player == players[0] else players[0]
            row = action["row"]
            col = action["col"]
            state["boards"][player]["shots"].append([row, col])
            if not self.is_game_over(state):
                opp_cells = _all_ship_cells_set(state["boards"][opponent]["ships"])
                if (row, col) not in opp_cells:
                    state["current_turn"] = opponent
                # hit: current_turn stays — player fires again

        return state

    def get_winner(self, state: dict) -> str | None:
        if state["phase"] != "battle":
            return None
        players = self._players(state)
        for player in players:
            opponent = players[1] if player == players[0] else players[0]
            opp_ship_cells = _all_ship_cells_set(state["boards"][opponent]["ships"])
            if not opp_ship_cells:
                continue
            my_shots = {tuple(s) for s in state["boards"][player]["shots"]}
            if opp_ship_cells.issubset(my_shots):
                return player
        return None

    def is_game_over(self, state: dict) -> bool:
        if state["phase"] != "battle":
            return False
        return self.get_winner(state) is not None

    def render_state_for_player(self, state: dict, player: str) -> dict:
        if not state.get("boards"):
            return {
                "phase": "placement", "current_turn": None,
                "i_am_ready": False, "ready_count": 0,
                "my_ships": [], "my_shots": [], "incoming": [],
                "opponent_ships": [], "sunk_my": [], "sunk_opponent": [],
            }
        players = self._players(state)
        opponent = players[1] if player == players[0] else players[0]

        my_board = state["boards"][player]
        opp_board = state["boards"][opponent]

        my_ship_cells = _all_ship_cells_set(my_board["ships"])
        opp_ship_cells = _all_ship_cells_set(opp_board["ships"])
        my_shot_set = {tuple(s) for s in my_board["shots"]}
        opp_shot_set = {tuple(s) for s in opp_board["shots"]}

        my_shots_annotated = [
            {"row": r, "col": c, "hit": (r, c) in opp_ship_cells}
            for r, c in my_board["shots"]
        ]
        incoming_annotated = [
            {"row": r, "col": c, "hit": (r, c) in my_ship_cells}
            for r, c in opp_board["shots"]
        ]

        sunk_my = [
            ship["type"]
            for ship in my_board["ships"]
            if all(tuple(cell) in opp_shot_set for cell in ship["cells"])
        ]
        sunk_opponent = [
            ship["type"]
            for ship in opp_board["ships"]
            if all(tuple(cell) in my_shot_set for cell in ship["cells"])
        ]

        return {
            "phase": state["phase"],
            "current_turn": state.get("current_turn"),
            "i_am_ready": player in state.get("ready", []),
            "ready_count": len(state.get("ready", [])),
            "my_ships": my_board["ships"],
            "my_shots": my_shots_annotated,
            "incoming": incoming_annotated,
            "opponent_ships": opp_board["ships"] if self.is_game_over(state) else [],
            "sunk_my": sunk_my,
            "sunk_opponent": sunk_opponent,
        }
