from poker.card import Card, Suit
from poker.hand_eval import evaluate_best, compare, STRAIGHT

def test_straight_flush_beats_quads():
    sf = evaluate_best([
        Card(9, Suit.HEARTS),
        Card(10, Suit.HEARTS),
        Card(11, Suit.HEARTS),
        Card(12, Suit.HEARTS),
        Card(13, Suit.HEARTS),
        Card(2, Suit.CLUBS),
        Card(3, Suit.DIAMONDS),
    ])
    quads = evaluate_best([
        Card(14, Suit.SPADES),
        Card(14, Suit.HEARTS),
        Card(14, Suit.DIAMONDS),
        Card(14, Suit.CLUBS),
        Card(5, Suit.HEARTS),
        Card(7, Suit.HEARTS),
        Card(9, Suit.SPADES),
    ])
    assert compare(sf, quads) > 0

def test_wheel_straight():
    hv = evaluate_best([
        Card(5, Suit.CLUBS),
        Card(4, Suit.DIAMONDS),
        Card(3, Suit.SPADES),
        Card(2, Suit.HEARTS),
        Card(14, Suit.CLUBS),
        Card(13, Suit.DIAMONDS),
        Card(12, Suit.SPADES),
    ])
    assert hv[0] == STRAIGHT
    assert hv[1][0] == 5
