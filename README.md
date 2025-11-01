# Poker Trainer & Bot (Python, Eclipse/PyDev)

This is a **Python** starter for your chess.com‑style poker project:

- Heads‑up Texas Hold’em vs a simple **equity bot** (console MVP).
- **Strategy simulator** (Monte Carlo equity / starting hand EV).
- Clean, dependency‑light core (only `pytest` for tests).

## Run quickly (no Eclipse)

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Git Bash
source .venv/Scripts/activate
pip install -U pip
pip install -r requirements.txt

# Play vs bot (console)
python -m poker.cli_play

# Strategy simulator (AA vs random, 20k trials)
python -m poker.sim_cli 20000

# Run tests
pytest -q
```

---

## Use in **Eclipse** (PyDev)

1. **Install PyDev**: *Help → Eclipse Marketplace… → search “PyDev” → Install*.
2. **Set Python**: *Window → Preferences → PyDev → Interpreters → Python Interpreter → New…*  
   Point to your Python 3.11/3.12 `python.exe` (e.g., `C:\Users\Saidou\AppData\Local\Programs\Python\Python312\python.exe`).
3. **Create a virtual env** (recommended):
   ```bash
   cd C:\Users\Saidou\git\repository5\poker-chesscom-py
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # or: source .venv/Scripts/activate
   pip install -r requirements.txt
   ```
   In Eclipse: *Project → Properties → PyDev - Interpreter/Grammar* → choose your `.venv` interpreter.
4. **Import the project**:
   - *File → New → PyDev Project*  
     - Project name: `poker-chesscom-py`  
     - **Uncheck** “Use default” → **Location**: this folder path.  
     - Grammar: Python 3.x  
     - **Finish**
   - (Or: *File → Import… → General → Existing Projects into Workspace* and select this folder, then set it to a PyDev project: Right‑click → *Configure → Convert to PyDev Project*).
5. **Run**:
   - Right‑click `poker/cli_play.py` → *Run As → Python Run* (play)
   - Right‑click `poker/sim_cli.py` → *Run As → Python Run* (sim)

---

## Roadmap

- [ ] Add FastAPI server for “online vs bot” (`/api/new_game`, `/api/act`) + simple web UI.
- [ ] Stronger bot (preflop ranges, pot‑odds, bluffing freq).
- [ ] Dataviz for strategy drills (EV by hand class, board texture).
- [ ] Persistence & ratings.nto `odds`/`suggest`.

