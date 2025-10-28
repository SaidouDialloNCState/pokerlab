from typing import List, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, getcontext
from .deck import Deck
from .card import Card, RANK_NAME
from .hand_eval import evaluate_best, compare, STRAIGHT_FLUSH, FOUR_KIND, FULL_HOUSE, FLUSH, STRAIGHT, THREE_KIND, TWO_PAIR, ONE_PAIR, HIGH_CARD
from .bot import decide
from .promptctx import record_prompt_context
from .ui import fmt_cards, console
from .suggest import suggest_action
from .equity import estimate_equity

getcontext().prec = 28

@dataclass
class GameConfig:
    variant: str            # 'holdem' | 'plo' | 'custom'
    hole_cards: int         # e.g., 2 for HE, 4 for PLO
    row_sizes: List[int]    # e.g., [3,1,1] for HE/PLO; custom like [2,2,1] etc.
    board_target_size: int  # sum(row_sizes)

def _to_money(s: str) -> Decimal:
    try:
        v = Decimal(s)
    except Exception:
        return Decimal("0")
    return v.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

def _fmt(x: Decimal) -> str:
    return f"${x:.2f}"

def _fmt_cards(cards: List[Card]) -> str:
    return ", ".join(str(c) for c in cards) if cards else "(no cards)"

def _hand_name(hv):
    cat, tb = hv
    if cat == STRAIGHT_FLUSH: return f"Straight Flush, high {RANK_NAME[tb[0]]}"
    if cat == FOUR_KIND:      return f"Four of a Kind, {RANK_NAME[tb[0]]}s"
    if cat == FULL_HOUSE:     return f"Full House, {RANK_NAME[tb[0]]}s over {RANK_NAME[tb[1]]}s"
    if cat == FLUSH:          return f"Flush, high {RANK_NAME[tb[0]]}"
    if cat == STRAIGHT:       return f"Straight, high {RANK_NAME[tb[0]]}"
    if cat == THREE_KIND:     return f"Three of a Kind, {RANK_NAME[tb[0]]}s"
    if cat == TWO_PAIR:       return f"Two Pair, {RANK_NAME[tb[0]]}s and {RANK_NAME[tb[1]]}s"
    if cat == ONE_PAIR:       return f"Pair of {RANK_NAME[tb[0]]}s"
    return f"{RANK_NAME[tb[0]]} High"

def _eval_variant_for(config: GameConfig) -> str:
    return "plo" if config.variant == "plo" else "holdem"

def play_hand_console(
    hero_stack: Decimal,
    bot_names: List[str],
    bot_levels: List[int],
    bot_stacks: List[Decimal],
    config: GameConfig,
    input_fn=input,
    print_fn=print
) -> Tuple[Decimal, List[Decimal]]:
    """Multi-player hand, one-bet-per-street (no raises). Seats: You (0), then bots."""
    n_bots = len(bot_names)
    stacks = [hero_stack] + bot_stacks[:]  # copy
    in_hand = [True] * (1 + n_bots)

    deck = Deck()
    board: List[Card] = []
    pot = Decimal("0.00")

    # Blinds: Hero SB $1, Bot0 BB $2 (if exists)
    if n_bots >= 1:
        sb = min(stacks[0], Decimal("1.00")); stacks[0] -= sb; pot += sb
        bb = min(stacks[1], Decimal("2.00")); stacks[1] -= bb; pot += bb

    # Deal hole cards
    holes: List[List[Card]] = [[deck.deal() for _ in range(config.hole_cards)] for _ in range(1 + n_bots)]

    print_fn(f"=== {config.variant.upper()} — One bet per street ===")
    print_fn(f"Players: You + {n_bots} opponents")
    print_fn(f"Your hand: {_fmt_cards(holes[0])}")

    eval_variant = _eval_variant_for(config)

    def max_bet_for(player_idx: int) -> Decimal:
        my = stacks[player_idx]
        others = [stacks[j] for j in range(1 + n_bots) if j != player_idx and in_hand[j]]
        return min([my] + others) if others else my

    def live_opponents_for(idx: int) -> int:
        return sum(1 for j in range(1 + n_bots) if j != idx and in_hand[j])

    def cheat_odds():
        # Compute hero equity vs remaining live opponents
        n_live_opp = live_opponents_for(0)
        eq = estimate_equity(
            holes[0],
            board,
            trials=1500,
            n_opponents=max(1, n_live_opp),
            eval_variant=eval_variant,
            board_target_size=config.board_target_size
        )
        print_fn(f"Cheat: your win odds ≈ {eq*100:.1f}% vs {n_live_opp} opponent(s).")

    def read_input(prompt: str) -> str:
        # support the 'ODDS' cheat at any prompt
        while True:
            s = input_fn(prompt)
            if isinstance(s, str) and s.strip().lower() == "odds":
                cheat_odds()
                continue
            return s

    def street(name: str, add_cards: int) -> bool:
        nonlocal pot
        for _ in range(add_cards):
            board.append(deck.deal())
        print_fn(f"{name} | Board: {_fmt_cards(board)}")

        bet_made = False
        bet_size = Decimal("0.00")
        bettor = -1
        acted_before_bet = [False]*(1+n_bots)

        # First pass: seat order, bet may occur here
        for idx in range(1 + n_bots):
            if not in_hand[idx] or stacks[idx] <= 0:
                continue
            if not bet_made:
                if idx == 0:
                    a = read_input("Action (C=check, B=bet, F=fold): ").strip().lower()
                    if a in ("f","fold"):
                        in_hand[0] = False
                        print_fn("You fold.")
                        # If only one left, end immediately
                        if sum(1 for i in range(1+n_bots) if in_hand[i]) == 1:
                            winner = next(i for i in range(1+n_bots) if in_hand[i])
                            if winner == 0:
                                print_fn(f"Everyone folded. You win {_fmt(pot)}.")
                                stacks[0] += pot
                            else:
                                print_fn(f"Everyone folded. {bot_names[winner-1]} wins {_fmt(pot)}.")
                                stacks[winner] += pot
                            return True
                        acted_before_bet[idx] = True
                        continue
                    if a in ("b","bet"):
                        maxb = max_bet_for(0)
                        if maxb < Decimal("0.01"):
                            print_fn("You cannot bet (no chips behind). You check.")
                            acted_before_bet[idx] = True
                            continue
                        s = read_input(f"Enter bet amount (max {_fmt(maxb)}): ").strip()
                        amt = _to_money(s)
                        if not (Decimal("0.01") <= amt <= maxb):
                            print_fn("Invalid amount. Treated as check.")
                            acted_before_bet[idx] = True
                            continue
                        stacks[0] -= amt; pot += amt
                        bet_made = True; bet_size = amt; bettor = 0
                        print_fn(f"You bet {_fmt(amt)}")
                    else:
                        print_fn("You check.")
                        acted_before_bet[idx] = True
                else:
                    live_opp = live_opponents_for(idx)
                    d = decide(bot_levels[idx-1], holes[idx], board if board else None, False, live_opp, eval_variant, config.board_target_size)
                    if d == "BET":
                        amt = min(Decimal("4.00"), max_bet_for(idx))
                        if amt < Decimal("0.01"):
                            print_fn(f"{bot_names[idx-1]} checks.")
                            acted_before_bet[idx] = True
                        else:
                            stacks[idx] -= amt; pot += amt
                            bet_made = True; bet_size = amt; bettor = idx
                            print_fn(f"{bot_names[idx-1]} bets {_fmt(amt)}")
                    else:
                        print_fn(f"{bot_names[idx-1]} checks.")
                        acted_before_bet[idx] = True
            else:
                if idx == 0:
                    a = read_input("Action (C=call, F=fold): ").strip().lower()
                    if a in ("c","call"):
                        call = min(stacks[0], bet_size)
                        stacks[0] -= call; pot += call
                        print_fn(f"You call {_fmt(call)}")
                    else:
                        in_hand[0] = False
                        print_fn("You fold.")
                else:
                    live_opp = live_opponents_for(idx)
                    d = decide(bot_levels[idx-1], holes[idx], board if board else None, True, live_opp, eval_variant, config.board_target_size)
                    if d == "CALL":
                        call = min(stacks[idx], bet_size)
                        stacks[idx] -= call; pot += call
                        print_fn(f"{bot_names[idx-1]} calls {_fmt(call)}")
                    else:
                        in_hand[idx] = False
                        print_fn(f"{bot_names[idx-1]} folds.")

        # Second pass: players who acted before a later bet must respond
        if bet_made:
            for idx in range(0, bettor):
                if not in_hand[idx] or stacks[idx] <= 0:
                    continue
                if acted_before_bet[idx]:
                    if idx == 0:
                        a = read_input("Action (C=call, F=fold): ").strip().lower()
                        if a in ("c","call"):
                            call = min(stacks[0], bet_size)
                            stacks[0] -= call; pot += call
                            print_fn(f"You call {_fmt(call)}")
                        else:
                            in_hand[0] = False
                            print_fn("You fold.")
                    else:
                        live_opp = live_opponents_for(idx)
                        d = decide(bot_levels[idx-1], holes[idx], board if board else None, True, live_opp, eval_variant, config.board_target_size)
                        if d == "CALL":
                            call = min(stacks[idx], bet_size)
                            stacks[idx] -= call; pot += call
                            print_fn(f"{bot_names[idx-1]} calls {_fmt(call)}")
                        else:
                            in_hand[idx] = False
                            print_fn(f"{bot_names[idx-1]} folds.")

        # If only one player remains, award pot
        if sum(1 for i in range(1+n_bots) if in_hand[i]) == 1:
            winner = next(i for i in range(1+n_bots) if in_hand[i])
            if winner == 0:
                print_fn(f"Everyone folded. You win {_fmt(pot)}.")
                stacks[0] += pot
            else:
                print_fn(f"Everyone folded. {bot_names[winner-1]} wins {_fmt(pot)}.")
                stacks[winner] += pot
            return True
        return False

    # Streets per config
    if street("Preflop", 0): return stacks[0], stacks[1:]
    # Name rows nicely for standard 3-1-1, else generic
    if config.row_sizes == [3,1,1]:
        labels = ["Flop","Turn","River"]
    else:
        labels = [f"Row {i+1}" for i in range(len(config.row_sizes))]
    for lab, add in zip(labels, config.row_sizes):
        if street(lab, add): return stacks[0], stacks[1:]

    # Showdown
    results = []
    for i in range(1+n_bots):
        if in_hand[i]:
            # Evaluate based on variant
            if config.variant == "plo":
                # use 2-from-hole + 3-from-board: re-use equity evaluator’s PLO rule
                from itertools import combinations
                best = None
                for h2 in combinations(holes[i], 2):
                    for b3 in combinations(board, 3):
                        hv = evaluate_best(list(h2)+list(b3))
                        if best is None or compare(hv, best) > 0:
                            best = hv
                hv = best
            else:
                hv = evaluate_best(holes[i] + board)
            results.append((i, hv))

    # Find winners
    winners = []
    best = None
    for i, hv in results:
        if best is None or compare(hv, best[1]) > 0:
            best = (i, hv)
            winners = [i]
        elif compare(hv, best[1]) == 0:
            winners.append(i)

    print_fn("Showdown!")
    for i, hv in results:
        name = "You" if i == 0 else bot_names[i-1]
        print_fn(f"  {name}: {_hand_name(hv)}")

    share = (pot / Decimal(len(winners))).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    remainder = pot - share*Decimal(len(winners))
    for wid in winners:
        stacks[wid] += share
    stacks[winners[0]] += remainder  # cents remainder

    if len(winners) == 1:
        name = "You" if winners[0] == 0 else bot_names[winners[0]-1]
        hvw = next(hv for i,hv in results if i==winners[0])
        print_fn(f"{name} wins {_fmt(pot)} with {_hand_name(hvw)}.")
    else:
        names = ", ".join(("You" if w==0 else bot_names[w-1]) for w in winners)
        print_fn(f"Split pot among: {names}.")

    return stacks[0], stacks[1:]
