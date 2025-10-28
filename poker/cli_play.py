from decimal import Decimal, ROUND_DOWN
from typing import List, Dict, Any
import os
from .engine import play_hand_console, GameConfig
from .promptctx import get_prompt_context
from .names import random_names
from .equity import estimate_equity
from .history import Recorder
from .suggest import suggest_action
from .ui import stats_panel

WELCOME = """Welcome to MIMO'S CASINO — where we go all in, all night.

Cheats: type 'odds' or 'suggest' during hands.
Type 'cheats' anytime for a quick explanation. Type 'how' anytime for controls.
Global: type 'exit' to quit, 'reset' to restart, or 'leave' to return to mode select.
"""

class ResetGame(Exception): pass
class LeaveToMenu(Exception): pass

def controls_help():
    print("""
=== CONTROLS ===
Cheats : Type 'odds' or 'suggest' during hands; type 'cheats' for a quick explainer.
Global : Type 'exit' to quit, 'reset' to restart, or 'leave' to return to mode select.
Help   : Type 'how' anytime to see this controls panel.
""")


def cheats_help():
    print("""
=== CHEATS HELP ===
ODDS   : shows your approximate chances to win/tie (Monte Carlo).
SUGGEST: recommends an action (BET/CHECK or CALL/FOLD) based on equity/heuristics.
Tip: Use SUGGEST at the action prompt (C/B/F). At amount prompts, enter a number.
""")


def ask(prompt: str) -> str:
    """Global input handler with cheats/help and numeric bet validation."""
    while True:
        s_in = input(prompt)
        t = s_in.strip().lower()

        # globals
        if t == "exit":  raise SystemExit
        if t == "reset": raise ResetGame
        if t == "leave": raise LeaveToMenu
        if t == "cheats":
            try: cheats_help()
            except Exception: print("odds shows equity; suggest gives action advice.")
            continue
        if t == "how":
            try: controls_help()
            except Exception: print("Controls: cheats (odds/suggest), exit/reset/leave.")
            continue

        # Action-prompt cheats
        if "action (" in prompt.lower():
            if t in ("suggest","s") or t in ("odds","o"):
                from .promptctx import get_prompt_context
                from .equity import estimate_equity
                from .suggest import suggest_action
                ctx = get_prompt_context()
                hole = ctx.get("hole")
                bd   = ctx.get("board")
                cfg  = ctx.get("config")
                stacks = ctx.get("stacks")
                # verify hero hand exists and is a list of Cards
                ok_hero = isinstance(hole, list) and len(hole) in (2,4) and all(hasattr(c,'rank') for c in hole)
                if not ok_hero or cfg is None:
                    print("suggest unavailable right now." if t.startswith("s") else "odds unavailable right now.")
                    continue
                # live opps
                try:
                    n_live = max(1, sum(1 for x in (stacks or [0,0]) [1:] if (isinstance(x,(int,float)) or hasattr(x,'__float__')) and float(x) > 0))
                except Exception:
                    n_live = 1
                if t.startswith("s"):
                    if getattr(cfg, "variant", "holdem") == "custom":
                        print("Cheat 'suggest' is not active for custom.")
                        continue
                    try:
                        action, why = suggest_action(cfg.variant, hole, bd, n_live, False)
                        print(f"suggest: {action.lower()} — {why}")
                    except Exception as e:
                        print(f"suggest unavailable: {e}")
                    continue
                else:  # odds
                    try:
                        eq = estimate_equity(hole, bd, trials=1200, n_opponents=n_live)
                        print(f"odds: win≈{eq:.1%} vs {n_live} opp(s)")
                    except Exception as e:
                        print(f"odds unavailable: {e}")
                    continue

        # bet validation
        if "enter bet amount (max $" in prompt.lower():
            import re as _re
            from decimal import Decimal as _D, ROUND_DOWN
            m = _re.search(r"max \$([0-9]+(?:\.[0-9]{1,2})?)", prompt, flags=_re.I)
            max_ok = None
            if m:
                try: max_ok = _D(m.group(1)).quantize(_D("0.01"), rounding=ROUND_DOWN)
                except Exception: max_ok = None
            try:
                val = _D(s_in).quantize(_D("0.01"), rounding=ROUND_DOWN)
            except Exception:
                print("Invalid. Try again.")
                continue
            if val <= 0:
                print("Invalid. Try again.")
                continue
            if max_ok is not None and val > max_ok:
                print("Amount exceeds maximum. Try again.")
                continue
            return str(val)

        return s_in


def _money_str(x: Decimal) -> str:
    return f"${x:.2f}"

def _to_money(s: str) -> Decimal:
    try:
        v = Decimal(s)
    except Exception:
        return Decimal("0")
    return v.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

def _how_to_play():
    print("""
=== HOW TO PLAY (Quick Guide) ===
• Hold'em: 2 hole; Flop(3) Turn(1) River(1) — best 5 wins.
• PLO: 4 hole; must use exactly 2 from hand + 3 from board.
• Custom: choose hole size and board rows (up to 5 rows).
Controls: C=check/call, B=bet, F=fold. One bet per street (no raises).
Cheats: 'odds' or 'suggest' during prompts. Type 'cheats' anytime for a quick explanation. Type 'how' anytime for controls. Type 'how' anytime for controls. Type 'how' anytime for controls. Global: 'exit' | 'reset' | 'leave' (back to mode select).
""")

def _pick_levels(n: int):
    while True:
        s = ask(f"Enter levels for {n} opponents (1-7) separated by spaces, or 'ALL 7': ").strip()
        up = s.upper()
        if up.startswith("ALL"):
            parts = up.split()
            if len(parts) == 2 and parts[1].isdigit():
                lvl = int(parts[1])
                if 1 <= lvl <= 7:
                    return [lvl]*n
        parts = s.split()
        if len(parts) == n and all(p.isdigit() and 1 <= int(p) <= 7 for p in parts):
            return [int(p) for p in parts]
        print("Invalid entry. Example: 'ALL 7' or '3 5 5 2'.")

def _pick_mode_and_config():
    while True:
        m = ask("Choose mode: (1) Texas Hold'em  (2) Pot-Limit Omaha  (3) Custom  (4) Sit-n-Go : ").strip()
        if m == "1":
            return "cash", GameConfig(variant="holdem", hole_cards=2, row_sizes=[3,1,1], board_target_size=5)
        if m == "2":
            return "cash", GameConfig(variant="plo", hole_cards=4, row_sizes=[3,1,1], board_target_size=5)
        if m == "3":
            while True:
                s = ask("Hole cards per player (1-7): ").strip()
                if s.isdigit() and 1 <= int(s) <= 7:
                    hole = int(s); break
                print("Enter 1..7.")
            while True:
                s = ask("How many board rows? (1-5): ").strip()
                if s.isdigit() and 1 <= int(s) <= 5:
                    rows = int(s); break
                print("Enter 1..5.")
            while True:
                s = ask(f"Enter cards per row (space-separated, {rows} numbers): ").strip()
                parts = s.split()
                if len(parts) == rows and all(p.isdigit() and 1 <= int(p) <= 5 for p in parts):
                    sizes = [int(p) for p in parts]; break
                print("Invalid. Example: 3 1 1")
            board_total = sum(sizes)
            return "cash", GameConfig(variant="custom", hole_cards=hole, row_sizes=sizes, board_target_size=board_total)
        if m == "4":
            return "sng", GameConfig(variant="holdem", hole_cards=2, row_sizes=[3,1,1], board_target_size=5)
        print("Please enter 1, 2, 3 or 4.")

def session_cash(bank: Decimal) -> Decimal:
    # Opponents
    while True:
        s = ask("How many opponents at the table? (1-7): ").strip()
        if s.isdigit() and 1 <= int(s) <= 7:
            n = int(s); break
        print("Please enter 1..7.")
    levels = _pick_levels(n)
    names = random_names(n, exclude={"You"})

    # Buy-in from bank
    wallet = bank
    while True:
        bi = _to_money(ask(f"Pick your buy-in (min $10.00, up to your bank {_money_str(wallet)}): ").strip())
        if Decimal("10.00") <= bi <= wallet:
            break
        print("Invalid buy-in.")
    wallet -= bi
    hero = bi
    bot_stacks = [Decimal("500.00")]*n
    print(f"You sit with {_money_str(hero)}. Bank left: {_money_str(wallet)}")
    print("Opponents:")
    for i, nm in enumerate(names):
        print(f"  - {nm} (Level {levels[i]})")

    # Stats
    stats = {"hands": 0, "vpip_n": 0, "pfr_n": 0, "sd_wins": 0}
    profit_deltas: List[float] = []
    top_pots: List[float] = []

    dealer_idx = 0
    rec = Recorder()

    try:
        while True:
            before = hero
            __res = play_hand_console(hero, names, levels, bot_stacks, _current_config, input_fn=ask, print_fn=print)

            # Accept 2/3/4-tuple returns from play_hand_console

            dealer_idx_update = None

            handinfo = {}

            if isinstance(__res, tuple):

                if len(__res) == 4:

                    hero, bot_stacks, dealer_idx_update, handinfo = __res

                elif len(__res) == 3:

                    hero, bot_stacks, dealer_idx_update = __res

                elif len(__res) == 2:

                    hero, bot_stacks = __res

            else:

                hero, bot_stacks = __res, None

            if dealer_idx_update is not None:

                dealer_idx = dealer_idx_update
            after = hero
            profit_deltas.append(float(after - before))

            # Save history if available
            jpath = None
            if "record" in handinfo:
                jpath = rec.dump(handinfo["record"])
                pot_total = sum(float(p["amount"]) for p in handinfo["record"].pots)
                top_pots.append(pot_total)

            # Stats update
            stats["hands"] += 1
            acts = handinfo.get("explain", [])
            preflop = [a for a in acts if a.street == "Preflop"]
            if any(a.seat == 0 and a.type in ("CALL", "BET") for a in preflop):
                stats["vpip_n"] += 1
            if any(a.seat == 0 and a.type == "BET" for a in preflop):
                stats["pfr_n"] += 1
            if any(a.type == "SHOWDOWN" and a.seat == 0 for a in acts) and after > before:
                stats["sd_wins"] += 1

            # Stacks line
            stacks_line = " | ".join(f"{names[i]}: {_money_str(bot_stacks[i])}" for i in range(len(names)))
            print(f"Stacks — You: {_money_str(hero)} | {stacks_line}  ||  Bank: {_money_str(wallet)}")

            # Post-hand menu: E=explain, R=replay last, 'leave' to menu (two-line prompt)
            while True:
                nxt = ask("""[E = Explanation, R = Replay last, type 'leave' to mode select]
Another hand? (y/n): """).strip().lower()
                if nxt == "e":
                    print("=== Hand Explanation ===")
                    for a in acts:
                        amt = f" {_money_str(Decimal(a.amount))}" if a.amount else ""
                        print(f"- {a.name} {a.type} on {a.street}{amt}")
                    continue
                if nxt == "r":
                    if jpath:
                        os.system(f'python -m poker.replay "{jpath}"')
                    else:
                        print("No recorded hand to replay.")
                    continue
                break

            if not nxt.startswith("y"):
                wallet += hero
                hero = Decimal("0.00")
                denom = max(1, stats["hands"])
                vpip = stats["vpip_n"] / denom
                pfr  = stats["pfr_n"] / denom
                stats_out = {"hands": stats["hands"], "vpip": vpip, "pfr": pfr, "sd_wins": stats["sd_wins"]}
                top3 = sorted(top_pots, reverse=True)[:3]
                stats_panel(stats_out, profit_deltas, top3)
                print(f"You cashed out. Total bank: {_money_str(wallet)}")
                return wallet
    except LeaveToMenu:
        # Cash out and return updated bank to the caller (no re-raise)
        wallet += hero
        print(f"\nCashing out {_money_str(hero)} and returning to menu. Total bank: {_money_str(wallet)}")
        hero = Decimal("0.00")
        return wallet
    except ResetGame:
        # Cash out then bubble up to restart the whole app
        wallet += hero
        print(f"\nCashing out {_money_str(hero)} and restarting. Total bank: {_money_str(wallet)}")
        hero = Decimal("0.00")
        raise
    return wallet

def session_sng(bank: Decimal) -> Decimal:
    print("=== Sit-n-Go === Equal stacks, winner takes 60%, 2nd 40% if 2+ players remain.")
    while True:
        s = ask("Players total (including you) (3-8) [6]: ").strip() or "6"
        if s.isdigit() and 3 <= int(s) <= 8:
            seats = int(s); break
        print("Enter 3..8.")
    n = seats - 1
    names = random_names(n, exclude={"You"})
    levels = _pick_levels(n)
    hero = Decimal("200.00")
    bot_stacks = [Decimal("200.00")] * n
    dealer_idx = 0
    config = GameConfig("holdem", 2, [3,1,1], 5)
    rec = Recorder()

    try:
        while True:
            __res = play_hand_console(hero, names, levels, bot_stacks, config, input_fn=ask, print_fn=print)

            # Accept 2/3/4-tuple returns from play_hand_console

            dealer_idx_update = None

            handinfo = {}

            if isinstance(__res, tuple):

                if len(__res) == 4:

                    hero, bot_stacks, dealer_idx_update, handinfo = __res

                elif len(__res) == 3:

                    hero, bot_stacks, dealer_idx_update = __res

                elif len(__res) == 2:

                    hero, bot_stacks = __res

            else:

                hero, bot_stacks = __res, None

            if dealer_idx_update is not None:

                dealer_idx = dealer_idx_update
            if "record" in handinfo:
                rec.dump(handinfo["record"])
            print("Stacks:", "You:", _money_str(hero), "|",
                  " | ".join(f"{names[i]}: {_money_str(bot_stacks[i])}" for i in range(n)))
            cont = ask("""[type 'leave' to mode select]
Next hand? (y/n): """).strip().lower()
            if not cont.startswith("y"):
                print(f"Leaving Sit-n-Go. Your bank is {_money_str(bank)}")
                return bank
    except LeaveToMenu:
        print(f"\nLeaving Sit-n-Go. Your bank is {_money_str(bank)}")
        return bank
    except ResetGame:
        print(f"\nLeaving Sit-n-Go (reset). Your bank is {_money_str(bank)}")
        raise

def main():
    print(WELCOME)
    bank = Decimal("500.00")
    asked_howto = False  # ask only once per program run
    try:
        while True:
            try:
                if not asked_howto:
                    if ask("Read 'How to Play' first? (y/n): ").strip().lower().startswith("y"):
                        _how_to_play()
                    asked_howto = True  # don't ask again this run
                mode, config = _pick_mode_and_config()
                global _current_config
                _current_config = config
                if mode == "sng":
                    bank = session_sng(bank)
                else:
                    bank = session_cash(bank)
                print(f"\nBack to mode select. Total cash: {_money_str(bank)}")
            except LeaveToMenu:
                # Shouldn't usually get here now for cash; keep as safety.
                print(f"\nBack to mode select. Total cash: {_money_str(bank)}")
                continue
            except ResetGame:
                print(f"\n[Reset] Back to the beginning. Total cash: {_money_str(bank)}")
                continue
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting. Goodbye!")

if __name__ == "__main__":
    main()
