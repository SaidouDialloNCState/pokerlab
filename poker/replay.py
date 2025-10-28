import json, sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    if len(sys.argv) < 2:
        console.print("Usage: python -m poker.replay path/to/HAND.json")
        sys.exit(1)
    p = Path(sys.argv[1])
    data = json.loads(p.read_text(encoding="utf-8"))
    console.rule(f"[bold]Replay {data['hand_id']} ({data['variant']})[/bold]")
    console.print("Players:", ", ".join(f"{i}:{n}" for i,n in enumerate(data["seats"])))
    console.print("Board:", ", ".join(data["board"]) or "(none)")
    t = Table(show_header=True, header_style="bold")
    t.add_column("Seat"); t.add_column("Name"); t.add_column("Street"); t.add_column("Action"); t.add_column("Amount")
    for a in data["actions"]:
        t.add_row(str(a["seat"]), a["name"], a["street"], a["type"], a["amount"])
    console.print(t)
    console.print("Pots:", data.get("pots"))
    console.print("Winners:", data["winners"])
if __name__ == "__main__":
    main()
