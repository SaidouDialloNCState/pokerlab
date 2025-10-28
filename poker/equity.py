from typing import List, Optional
import random
from itertools import combinations
from .card import Card, Suit, RANKS
from .hand_eval import evaluate_best, compare

def _eval_holdem_like(hole: List[Card], board: List[Card]) -> tuple:
    # Standard: best 5 out of all cards
    return evaluate_best(hole + board)

def _eval_plo(hole: List[Card], board: List[Card]) -> tuple:
    # Must use EXACTLY 2 from hole and 3 from board
    best = None
    for h2 in combinations(hole, 2):
        for b3 in combinations(board, 3):
            hv = evaluate_best(list(h2) + list(b3))  # exactly 5 cards
            if best is None or compare(hv, best) > 0:
                best = hv
    return best

def estimate_equity(
    hero: List[Card],
    board: Optional[List[Card]],
    trials: int = 10000,
    n_opponents: int = 1,
    eval_variant: str = "holdem",
    board_target_size: Optional[int] = None
) -> float:
    """
    Monte Carlo equity vs n_opponents.
    Variants:
      - 'holdem' (default) and 'custom': best 5 out of all cards
      - 'plo': exactly 2 from hole + 3 from board
    Ties count as 0.5.
    """
    if board is None:
        board = []

    # Choose evaluator and target board size
    if eval_variant == "plo":
        eval_fn = _eval_plo
        target = 5 if board_target_size is None else board_target_size
    else:
        eval_fn = _eval_holdem_like
        target = 5 if board_target_size is None else board_target_size

    # Build deck minus used
    deck_full = [Card(rank=v, suit=s) for s in Suit for v in RANKS.values()]
    used = set(hero) | set(board)
    base_deck = [c for c in deck_full if c not in used]

    wins = 0
    ties = 0
    for _ in range(trials):
        deck = base_deck[:]
        random.shuffle(deck)
        idx = 0

        # deal opponents
        # assume opponents have same hole size as hero
        opp_holes = []
        hole_size = len(hero)
        for _k in range(n_opponents):
            opp_holes.append([deck[idx + i] for i in range(hole_size)])
            idx += hole_size

        # complete board
        b = list(board)
        while len(b) < target:
            b.append(deck[idx]); idx += 1

        hv = eval_fn(hero, b)
        # compare vs each opponent
        hero_best = True
        tie_seen = False
        for hole in opp_holes:
            ov = eval_fn(hole, b)
            c = compare(hv, ov)
            if c < 0:
                hero_best = False
                break
            elif c == 0:
                tie_seen = True
        if not hero_best:
            continue
        if tie_seen:
            ties += 1
        else:
            wins += 1

    return (wins + 0.5*ties) / max(1, trials)
