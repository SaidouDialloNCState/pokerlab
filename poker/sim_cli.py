from .card import Card, Suit
from .equity import estimate_equity
import sys

def main():
    trials = 10000
    if len(sys.argv) > 1:
        try:
            trials = max(1000, int(sys.argv[1]))
        except Exception:
            pass
    hero = [Card(14, Suit.SPADES), Card(14, Suit.HEARTS)]
    eq = estimate_equity(hero, board=None, trials=trials)
    print(f"Preflop equity of AA vs random over {trials:,} trials: {eq:.3f}")

if __name__ == "__main__":
    main()
