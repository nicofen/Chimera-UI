# Chimera‑UI

Chimera‑UI is the graphical interface layer for the Chimera trading system.  
It provides a clean, modular, and cinematic UI experience for interacting with live or simulated trading data.

## ✨ Features

- **Modular UI Architecture**  
  Designed around clean separation between backend logic and UI components.

- **Real‑time Visualization**  
  Displays trade history, signals, and performance metrics in a responsive interface.

- **File‑Driven Workflow**  
  Load JSON‑based trade data (e.g., `sample.json`) and instantly visualize it.

- **Lightweight Launcher**  
  Run the entire interface using a single entry point:  
  ```bash
  python main.py

## How to use
### 1. Clone the Repository

```bash
git clone https://github.com/nicofen/Chimera-UI.git
cd Chimera-UI```

### 2. Download dependencies
`pip install -r requirements.txt`

### 3. Run main.py
`python main/main.py`

### 4. Use temporary data
Use the file button to import the chimera_sample.json. Soon we will come out with the full Chimera, which will include the AI agents, but until then we have not put them in.

### Equity + Drawdown chart — 
the main view. Equity curve in teal with a fade-to-transparent area fill beneath it. Below a separator, the underwater drawdown chart bleeds red from zero — the deeper the fill, the worse the drawdown. Green and red dots mark individual trade exits on the equity line. Crosshair follows the mouse and shows exact equity and percentage return in the tab bar. The two charts are intentionally stacked rather than overlaid so both are readable at once.


### Rolling Sharpe chart — 
20-trade rolling Sharpe ratio, coloured teal above zero and red below. The fill makes it instantly obvious how long the strategy spent in negative risk-adjusted return territory. The amber dashed average R line gives a secondary reference.


### R-Multiple scatter — 
every trade as a dot, colour-coded by sector (blue=stocks, purple=crypto, amber=forex, pink=futures), plotted in chronological order. The amber dashed line shows the mean R across all trades. This is the most honest chart — it shows exactly how often the strategy hit its TP versus stopped out, and whether edge is consistent or clustered.

### Right sidebar — 
sector P&L bars (proportional, colour-coded), exit reason breakdown (TP hit vs trailing stop vs hard stop, in green/amber/red), sector colour legend for the scatter, and a live-scrolling list of the 8 most recent closed trades.

