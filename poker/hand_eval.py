from typing import List, Tuple
from .card import Card

STRAIGHT_FLUSH = 8
FOUR_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_KIND = 3
TWO_PAIR = 2
ONE_PAIR = 1
HIGH_CARD = 0

def _straight_high(counts: list[int]) -> int:
    run = 0
    for v in range(14, 2-1, -1):
        if counts[v] > 0:
            run += 1
            if run >= 5:
                return v + 4
        else:
            run = 0
    if counts[14] and counts[5] and counts[4] and counts[3] and counts[2]:
        return 5
    return 0

def _evaluate5(cards: List[Card]) -> Tuple[int, List[int]]:
    cnt = [0]*15
    s_cnt = [0]*4
    for c in cards:
        cnt[c.rank] += 1
        s_cnt[c.suit.value-1] += 1

    flush = False
    flush_suit = -1
    for s in range(4):
        if s_cnt[s] == 5:
            flush = True
            flush_suit = s
            break

    straight_high = _straight_high(cnt)

    if flush:
        cnt_flush = [0]*15
        for c in cards:
            if c.suit.value-1 == flush_suit:
                cnt_flush[c.rank] += 1
        sh = _straight_high(cnt_flush)
        if sh > 0:
            return (STRAIGHT_FLUSH, [sh])

    four = -1
    three = -1
    pairs: List[int] = []
    singles: List[int] = []
    for v in range(14, 1, -1):
        if cnt[v] == 4:
            four = v
        elif cnt[v] == 3:
            if v > three:
                three = v
        elif cnt[v] == 2:
            pairs.append(v)
        elif cnt[v] == 1:
            singles.append(v)

    if four > 0:
        return (FOUR_KIND, [four, singles[0]])

    if three > 0 and pairs:
        return (FULL_HOUSE, [three, pairs[0]])

    if flush:
        ranks_desc = [v for v in range(14, 1, -1) if cnt[v] > 0]
        return (FLUSH, ranks_desc)

    if straight_high > 0:
        return (STRAIGHT, [straight_high])

    if three > 0:
        tb = [three]
        tb.extend(singles[:2])
        return (THREE_KIND, tb)

    if len(pairs) >= 2:
        return (TWO_PAIR, [pairs[0], pairs[1], singles[0]])

    if len(pairs) == 1:
        tb = [pairs[0]]
        tb.extend(singles[:3])
        return (ONE_PAIR, tb)

    ranks_desc = [v for v in range(14, 1, -1) if cnt[v] > 0]
    return (HIGH_CARD, ranks_desc)

def evaluate_best(cards: List[Card]) -> Tuple[int, List[int]]:
    n = len(cards)
    if n < 5 or n > 7:
        raise ValueError("need 5..7 cards")
    best = None
    for a in range(n-4):
        for b in range(a+1, n-3):
            for c in range(b+1, n-2):
                for d in range(c+1, n-1):
                    for e in range(d+1, n):
                        cur = _evaluate5([cards[a], cards[b], cards[c], cards[d], cards[e]])
                        if best is None or compare(cur, best) > 0:
                            best = cur
    assert best is not None
    return best

def compare(a: Tuple[int, List[int]], b: Tuple[int, List[int]]) -> int:
    """Return +1 if a>b, 0 if equal, -1 if a<b."""
    if a[0] != b[0]:
        return 1 if a[0] > b[0] else -1
    x, y = a[1], b[1]
    for i in range(min(len(x), len(y))):
        if x[i] != y[i]:
            return 1 if x[i] > y[i] else -1
    if len(x) != len(y):
        return 1 if len(x) > len(y) else -1
    return 0
