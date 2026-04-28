import json
import os

class TradeHistory:
    def __init__(self, filename="trade_history.json"):
        self.filename = filename
        self.trades = []

        print("DEBUG: TradeHistory __init__ called")
        print("DEBUG: Loading trade history from:", self.filename)

        self.load()

    def load(self):
        print("DEBUG: File exists:", os.path.exists(self.filename))

        if not os.path.exists(self.filename):
            print("DEBUG: Creating new empty trade history file")
            with open(self.filename, "w") as f:
                json.dump([], f, indent=4)
            self.trades = []
            return

        try:
            with open(self.filename, "r") as f:
                self.trades = json.load(f)
            print("DEBUG: Loaded trades:", len(self.trades))
        except Exception as e:
            print("DEBUG: Failed to load trade history:", e)
            self.trades = []

    def save(self):
        print("DEBUG: Saving trade history:", len(self.trades))
        with open(self.filename, "w") as f:
            json.dump(self.trades, f, indent=4)

    def add_trade(self, trade):
        self.trades.append(trade)
        self.save()

    def get_all(self):
        return self.trades