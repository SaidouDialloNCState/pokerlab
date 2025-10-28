from typing import List
from .card import Card
from .equity import estimate_equity

# 1 = weakest/loose, 7 = strongest/tightest
BET_THR  = {1:0.55, 2:0.58, 3:0.60, 4:0.62, 5:0.64, 6:0.66, 7:0.68}
CALL_THR = {1:0.44, 2:0.46, 3:0.48, 4:0.50, 5:0.52, 6:0.54, 7:0.56}

def decide(
    level: int,
    hole: List[Card],
    board,
    facing_bet: bool,
    n_live_opponents: int,
    eval_variant: str,
    board_target_size: int
) -> str:
    # Multiway penalty: more opponents → need stronger equity
    add = max(0, n_live_opponents-1) * 0.04
    bthr = min(0.98, BET_THR.get(level, 4) + add)

