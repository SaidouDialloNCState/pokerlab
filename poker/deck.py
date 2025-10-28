import random
from .card import Card, Suit, RANKS

class Deck:
    def __init__(self) -> None:
        self.cards = [Card(rank=v, suit=s) for s in Suit for v in RANKS.values()]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if not self.cards:
            raise RuntimeError("Deck empty")
        return self.cards.pop()
