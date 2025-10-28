from __future__ import annotations
from typing import List, Optional, Tuple
from .card import Card
from .equity import estimate_equity

# ---------- Hold'em (equity-based) ----------
def _holdem_suggest(
    hole: List[Card],
    board: Optional[List[Card]],
    n_live_opponents: int,
    facing_bet: bool
) -> Tuple[str, str]:
    # Scale trials down as streets progress
    trials = 2000 // (1 + (0 if not board else len(board)))
    eq = estimate_equity(hole, board, trials=max(1200, trials), n_opponents=max(1, n_live_opponents))

    # Thresholds tighten as more opponents enter
    add = max(0, n_live_opponents - 1) * 0.04
    bet_thr  = min(0.98, 0.58 + add)
    call_thr = min(0.98, 0.46 + add)

    if not facing_bet:
        action = "BET" if eq >= bet_thr else "CHECK"
    else:
        action = "CALL" if eq >= call_thr else "FOLD"

    why = f"Equity ≈ {eq:.1%} vs {n_live_opponents} opp(s); bet≥{bet_thr:.0%}, call≥{call_thr:.0%}."
    return action, why

# ---------- PLO (preflop heuristic) ----------
_RANK_VALUE = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}

def _is_double_suited(cards: List[Card]) -> bool:
    counts = {}
    for c in cards: counts[c.suit] = counts.get(c.suit, 0) + 1
    return sum(1 for v in counts.values() if v >= 2) >= 2

def _is_single_suited(cards: List[Card]) -> bool:
    return any(sum(1 for c in cards if c.suit == s) >= 2 for s in {c.suit for c in cards})

def _pair_strength(vals: List[int]) -> float:
    p = {}
    for v in vals: p[v] = p.get(v, 0) + 1
    bonus = 0.0
    for v, cnt in p.items():
        if cnt >= 2:
            if v == 14: bonus += 0.22
            elif v == 13: bonus += 0.14
            elif v in (12, 11): bonus += 0.10
            elif v >= 9: bonus += 0.07
            else: bonus += 0.05
    return bonus

def _rundown_bonus(vals: List[int]) -> float:
    u = sorted(set(vals))
    best = cur = 1
    for i in range(1, len(u)):
        if u[i] == u[i-1] + 1: cur += 1
        else: best = max(best, cur); cur = 1
    best = max(best, cur)
    if best >= 4: return 0.15
    if best == 3: return 0.08
    if best == 2: return 0.04
    return 0.0

def _highcards_bonus(vals: List[int]) -> float:
    top2 = sorted(vals, reverse=True)[:2]
    s2 = sum(top2)
    if s2 >= 27: return 0.08
    if s2 >= 25: return 0.05
    if s2 >= 23: return 0.03
    return 0.0

def _gaps_penalty(vals: List[int]) -> float:
    v = sorted(set(vals), reverse=True)
    gaps = [v[i] - v[i+1] for i in range(len(v)-1)]
    big = sum(1 for g in gaps if g >= 3)
    return -0.05 * big

def _suit_penalty(cards: List[Card]) -> float:
    counts = {}
    for c in cards: counts[c.suit] = counts.get(c.suit, 0) + 1
    return -0.10 if any(v >= 4 for v in counts.values()) else 0.0

def _plo_preflop_score(hole: List[Card]) -> float:
    vals = [_RANK_VALUE[c.rank] for c in hole]
    score = 0.30
    score += 0.18 if _is_double_suited(hole) else (0.08 if _is_single_suited(hole) else 0.0)
    score += _pair_strength(vals)
    score += _rundown_bonus(vals)
    score += _highcards_bonus(vals)
    score += _gaps_penalty(vals)
    score += _suit_penalty(hole)
    return max(0.0, min(1.0, score))

def _plo_suggest(hole: List[Card], n_live_opponents: int, facing_bet: bool) -> Tuple[str, str]:
    s = _plo_preflop_score(hole)
    add = max(0, n_live_opponents - 1) * 0.04
    bet_thr  = min(0.98, 0.62 + add)
    call_thr = min(0.98, 0.52 + add)
    if not facing_bet:
        action = "BET" if s >= bet_thr else "CHECK"
    else:
        action = "CALL" if s >= call_thr else "FOLD"
    why = f"Preflop score {s:.2f} (ds/suited, pairs, rundowns, high cards) vs {n_live_opponents} opp(s)."
    return action, why

def suggest_action(
    variant: str,
    hole: List[Card],
    board: Optional[List[Card]],
    n_live_opponents: int,
    facing_bet: bool
) -> Tuple[str, str]:
    if variant == "holdem":
        return _holdem_suggest(hole, board, n_live_opponents, facing_bet)
    if variant == "plo":
        return _plo_suggest(hole, n_live_opponents, facing_bet)  # preflop heuristic
    raise NotImplementedError("suggest is not active for custom")
