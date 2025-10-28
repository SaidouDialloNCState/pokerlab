from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from decimal import Decimal
import json, csv, time, os

@dataclass
class Action:
    seat: int
    name: str
    street: str
    type: str    # CHECK/BET/CALL/FOLD/ALLIN/POST_SB/POST_BB/SHOWDOWN
    amount: str  # money string or ""
    meta: Dict[str,Any]

@dataclass
class HandRecord:
    hand_id: str
    variant: str
    seats: List[str]     # index 0 is "You"
    levels: List[int]    # for bots (0 for hero)
    stacks_start: List[str]
    stacks_end: List[str]
    board: List[str]
    pots: List[Dict[str,Any]]
    winners: List[int]
    actions: List[Action]

class Recorder:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(history_dir, exist_ok=True)

    def ts_id(self) -> str:
        return time.strftime("%Y%m%d-%H%M%S")

    def dump(self, rec: HandRecord):
        hid = rec.hand_id
        jpath = os.path.join(self.history_dir, f"{hid}.json")
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump({
                **asdict(rec),
                "actions":[asdict(a) for a in rec.actions]
            }, f, indent=2)
        # simple CSV summary (one row per hand)
        cpath = os.path.join(self.history_dir, "hands.csv")
        new = not os.path.exists(cpath)
        with open(cpath, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["hand_id","variant","players","winners","pot_total"])
            total = sum(Decimal(p["amount"]) for p in rec.pots)
            w.writerow([hid, rec.variant, len(rec.seats), "|".join(map(str, rec.winners)), f"{total:.2f}"])
        return jpath

def build_sidepots(contrib: List[Decimal], alive: List[bool]) -> List[Dict[str,Any]]:
    """
    contrib[i] = total amount contributed by seat i to the pot.
    alive[i]   = still in hand at showdown.
    Returns [{"amount": Decimal, "contesters":[seat_idx,...]}] in order.
    """
    # Unique non-zero contribution levels
    tiers = sorted({c for c in contrib if c > 0})
    pots = []
    prev = Decimal("0.00")
    for t in tiers:
        amount = Decimal("0.00")
        contesters = []
        for i, c in enumerate(contrib):
            layer = max(Decimal("0.00"), min(c, t) - prev)
            if layer > 0:
                amount += layer
                if alive[i]:
                    contesters.append(i)
        pots.append({"amount": amount, "contesters": contesters})
        prev = t
    return pots
