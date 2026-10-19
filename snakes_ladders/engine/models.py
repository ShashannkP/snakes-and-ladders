"""Domain Data Types (SDD 3.2, 3.6.2)"""

from dataclasses import dataclass
from enum import Enum

class Phase(Enum):
    AWAITING_ROLL = "awaiting_roll"
    ANIMATING = "animating"
    GAME_OVER = "game_over"
    
class Event(Enum):
    NONE = "none"
    SNAKE = "snake"
    LADDER = "ladder"
    OVERSHOOT = "overshoot"
    

@dataclass
class Player:
    name: str
    colour: str
    position: int = 0  # 0 = start position, outside the board


@dataclass(frozen=True)
class Standing:
    rank: int
    player_index: int
    name: str
    colour: str
    position: int

@dataclass
class GameState:
    players: list[Player]
    current_index: int = 0
    extra_turn_enabled: bool = False
    extra_rolls_used: int = 0
    last_roll: int | None = None
    phase: Phase = Phase.AWAITING_ROLL

@dataclass(frozen=True)
class TurnResult:
    """The entire state after one roll."""

    player_index: int
    roll: int
    from_pos: int
    landed_pos: int  
    final_pos: int
    event: Event
    extra_roll: bool
    winner_index: int | None
    next_index: int

