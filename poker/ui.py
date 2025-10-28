from rich.console import Console
from rich.table import Table
from rich.text import Text
from typing import List, Dict, Any
from .card import Card, RANK_NAME

console = Console()

SUIT_GLYPH = {"SPADES":"♠","CLUBS":"♣","HEARTS":"♥","DIAMONDS":"♦"}
RED_SUITS = {"HEARTS","DIAMONDS"}

def _rank_letter(c: Card) -> str:
    # Try mapping via RANK_NAME[int]; fallback to parsing "X OF SUIT"
    try:
        rn = RANK_NAME[getattr(c, "rank")]
    except Exception:
        rn = str(c).split(" OF ")[0].upper()
    mapping = {"ACE":"A","KING":"K","QUEEN":"Q","JACK":"J","10":"T"}
    if rn in mapping:
        return mapping[rn]
    return rn  # "2".."9" or already single-char

def _suit_name(c: Card) -> str:
    s = getattr(getattr(c, "suit", None), "name", None)
    if s:
        return s
    s = getattr(c, "suit_name", None)
    if s:
        return s
    parts = str(c).split(" OF ")
    if len(parts) == 2:
        return parts[1].strip().upper()
    return "SPADES"

def fmt_card(c: Card) -> Text:
    r = _rank_letter(c)
    sname = _suit_name(c)
    glyph = SUIT_GLYPH.get(sname, "♠")
    t = Text(f"{r}{glyph}")
    if sname in RED_SUITS:
        t.stylize("bold red")
    return t

def fmt_cards(cards: List[Card]) -> Text:
    out = Text()
    for i, c in enumerate(cards):
        if i: out.append(" ")
        out.append(fmt_card(c))
    return out

def header_hand(title: str, dealer_name: str, positions: Dict[int,str], names: List[str]):
    console.rule(f"[bold]{title}[/bold]")
    ring = Table.grid(expand=False)
    for idx, nm in enumerate(["You"] + names):
        pos = positions.get(idx, "")
        ring.add_row(f"{idx}. {nm}  [{pos}]")
    console.print(ring)
    console.print(f"Dealer: [bold]{dealer_name}[/bold]")

def show_board(stage: str, board: List[Card]):
    console.print(f"[bold]{stage}[/bold] | Board: ", fmt_cards(board) if board else Text("(no cards)"))

def announce(msg: str):
    console.print(msg)

def winner_line(name: str, pot_str: str, bold=True):
    if bold:
        console.print(f"[bold]{name} wins {pot_str}[/bold]")
    else:
        console.print(f"{name} wins {pot_str}")

def show_pots(pots: List[Dict[str,Any]]):
    table = Table(title="Side Pots", show_header=True, header_style="bold")
    table.add_column("#")
    table.add_column("Amount")
    table.add_column("Contested by")
    for i,p in enumerate(pots, start=1):
        table.add_row(str(i), f"${p['amount']:.2f}", ", ".join(str(x) for x in p["contesters"]))
    console.print(table)

def stats_panel(stats: Dict[str,Any], profit_points: List[float], top_pots: List[float]):
    console.rule("[bold]Session Stats[/bold]")
    console.print(f"Hands: {stats['hands']} | VPIP: {stats['vpip']:.0%} | PFR: {stats['pfr']:.0%} | Showdown wins: {stats['sd_wins']}")
    if profit_points:
        minv = min(profit_points); maxv = max(profit_points)
        span = max(1e-9, maxv-minv)
        width = 40
        scaled = [int((p-minv)/span*(width-1)) for p in profit_points]
        console.print("[bold]Profit graph[/bold] (per hand delta)")
        for x in scaled:
            console.print(" " * x + "*")
    if top_pots:
        console.print(f"Top pots: {', '.join(f'${x:.2f}' for x in top_pots)}")
