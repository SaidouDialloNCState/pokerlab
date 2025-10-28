from dataclasses import dataclass
from enum import Enum, auto

class Suit(Enum):
    CLUBS = auto()
    DIAMONDS = auto()
    HEARTS = auto()
    SPADES = auto()

RANKS = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14
}

RANK_NAME = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
    10: "10", 11: "JACK", 12: "QUEEN", 13: "KING", 14: "ACE"
}
SUIT_NAME = {
    Suit.CLUBS: "CLUBS",
    Suit.DIAMONDS: "DIAMONDS",
    Suit.HEARTS: "HEARTS",
    Suit.SPADES: "SPADES",
}

@dataclass(frozen=True, order=True)
class Card:
    rank: int  # 2..14
    suit: Suit

    def __str__(self) -> str:
        return f"{RANK_NAME[self.rank]} OF {SUIT_NAME[self.suit]}"
