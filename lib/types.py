
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SessionState(Enum):
    INIT = 0
    READY = 1
    CLOSED = 2
class PlayerState(Enum):
    INIT = 0
    READY = 1
    CLOSED = 2

# @dataclass
# class Topic:
#     id: int
#     name: str
#     player_id: str

# @dataclass
# class Player:
#     id: str
#     created_at: Any
#     name: str
#     first_name: str
#     last_name: str
#     state: PlayerState
#     session_id: str
#     topics: list[Topic]

# @dataclass
# class Session:
#     id: str
#     created_at: Any
#     invitation_code: str
#     state: SessionState
#     players: list[Player]




