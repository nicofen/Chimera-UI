# ==========================
# Chimera UI Example/Test 1
# ==========================

import json
import math
import numpy as np
from functools import partial

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QRect, QEasingCurve, QSize
)
from PySide6.QtGui import (
    QAction, QIcon, QColor, QFont
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTabWidget, QFrame,
    QScrollArea, QDockWidget, QSizePolicy
)

# Matplotlib → Qt embedding
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# ============================================================
#  COLOR PALETTE (converted from your JSX palette)
# ============================================================

def rgba(r, g, b, a):
    """Convert 0–255 RGBA to matplotlib 0–1 tuple."""
    return (r/255, g/255, b/255, a)

C = {
    "bg":      "#080a0b",
    "surface": "#0e1214",
    "panel":   "#131719",
    "border":  "#1e2428",
    "border2": "#263036",
    "dim":     "#3a444a",
    "muted":   "#5a6870",
    "text":    "#b8c8d0",
    "bright":  "#ddeef5",
    "teal":    "#00c8b4",
    "teal2":   "#00e6ce",
    "tealFill": rgba(0,200,180,0.12),
    "red":     "#e03050",
    "redFill": rgba(220,40,60,0.18),
    "amber":   "#e8a030",
    "green":   "#38c870",
    "blue":    "#3888e8",
    "purple":  "#9060e8",
    "sector": {
        "stocks":  "#3888e8",
        "crypto":  "#9060e8",
        "forex":   "#e8a030",
        "futures": "#e03878",
    },
    "reason": {
        "TP_HIT":        "#38c870",
        "TRAILING_STOP": "#e8a030",
        "STOP_HIT":      "#e03050",
    }
}

MONO = QFont("Menlo", 9)
SANS = QFont("IBM Plex Sans", 10)


# ============================================================
#  MATPLOTLIB CANVAS WRAPPER
# ============================================================

class MplCanvas(FigureCanvasQTAgg):
    """A matplotlib canvas embedded inside Qt."""
    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=C["surface"])
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(C["surface"])
        self.fig.subplots_adjust(left=0.06, right=0.99, top=0.97, bottom=0.05)

    def clear(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(C["surface"])
        self.fig.subplots_adjust(left=0.06, right=0.99, top=0.97, bottom=0.05)

import numpy as np
from matplotlib.patches import Polygon

# NOTE: assumes MplCanvas, C, rgba, MONO, SANS are already defined above

# ============================
# PART 1 — BUYING TAB SKELETON
# ============================

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal


class BuyingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from trade_history import TradeHistory
        self.trade_history = TradeHistory()
        self.equity_chart = None
        self.sharpe_chart = None
        self.scatter_chart = None

        self.mock_generator = MockEventGenerator()
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedHeight(40)
        self.stop_button.setEnabled(False)

        self.shutdown_button = QPushButton("Shutdown")
        self.shutdown_button.setFixedHeight(40)
        self.shutdown_button.setEnabled(False)
        self.start_button = QPushButton("Start")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_mainframe)

        button_style = """
        QPushButton {
            background-color: #1e1e1e;
            color: #d4af37;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #2a2a2a;
            border: 1px solid #d4af37;
            color: #f5d98c;
        }
        QPushButton:pressed {
            background-color: #111;
            border: 1px solid #8c6f1d;
            color: #d4af37;
        }
        """

        self.start_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        self.shutdown_button.setStyleSheet(button_style)

        self.equity_label = QLabel("Total Equity: $0.00")
        self.equity_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.equity_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.start_button)
        top_bar.addWidget(self.stop_button)
        top_bar.addWidget(self.shutdown_button)
        top_bar.addStretch()
        top_bar.addWidget(self.equity_label)
        self.stop_button.clicked.connect(self.stop_mainframe)
        self.shutdown_button.clicked.connect(self.shutdown_system)

        self.trade_grid = QGridLayout()
        self.trade_grid.setSpacing(12)

        trade_container = QWidget()
        trade_container.setLayout(self.trade_grid)

        self.trade_scroll = QScrollArea()
        self.trade_scroll.setWidgetResizable(True)
        self.trade_scroll.setWidget(trade_container)
        self.trade_scroll.setMinimumHeight(350)

        self.completed_sidebar = QVBoxLayout()
        self.completed_sidebar.addStretch()

        sidebar_frame = QFrame()
        sidebar_frame.setFrameShape(QFrame.StyledPanel)
        sidebar_frame.setLayout(self.completed_sidebar)
        sidebar_frame.setMinimumWidth(260)

        main_layout = QHBoxLayout()

        self.setLayout(main_layout)

        self.equity_timer = QTimer()
        self.equity_timer.timeout.connect(self.update_equity)
        self.equity_timer.start(5000)  # every 5 seconds

        self.trade_widgets = []
        self.completed_widgets = []
        self.completed_sidebar_layout = QVBoxLayout()
        self.completed_sidebar_layout.setSpacing(8)
        self.completed_sidebar_layout.addStretch()

        sidebar_container = QWidget()
        sidebar_container.setLayout(self.completed_sidebar_layout)

        self.completed_scroll = QScrollArea()
        self.completed_scroll.setWidgetResizable(True)
        self.completed_scroll.setWidget(sidebar_container)
        self.completed_scroll.setMinimumWidth(260)
        self.completed_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mainframe_thread = MainframeThread()
        self.listener_thread = TradeEventListener(event_file="mock_events.jsonl")

        self.listener_thread.new_trade_signal.connect(self.add_trade)
        self.listener_thread.update_trade_signal.connect(self.update_trade)
        self.listener_thread.close_trade_signal.connect(self.complete_trade)

        left_side = QVBoxLayout()
        left_side.addLayout(top_bar)
        left_side.addWidget(self.trade_scroll)

        main_layout.addLayout(left_side)
        main_layout.addWidget(self.completed_scroll)
        self.rebuild_from_history()
    def attach_charts(self, equity_chart, sharpe_chart, scatter_chart):
        self.equity_chart = equity_chart
        self.sharpe_chart = sharpe_chart
        self.scatter_chart = scatter_chart
    def rebuild_from_history(self):
        for trade in self.trade_history.get_all():
            widget = CompletedTradeWidget(trade)
            self.completed_sidebar_layout.insertWidget(
                self.completed_sidebar_layout.count() - 1,
                widget
            )
            self.completed_widgets.append(widget)

        # TODO: hook in equity, sharpe, scatter widgets here
    def update_equity_display(self):
        equity = self.fetch_equity_value()
        self.equity_label.setText(f"Equity: ${equity:,.2f}")
    def stop_mainframe(self):
        print("Stopping mainframe and listener...")

        self.listener_thread.running = False
        self.listener_thread.quit()
        self.listener_thread.wait()
        self.mock_generator.running = False
        self.mock_generator.quit()
        self.mock_generator.wait()

        # Stop mainframe thread
        self.mainframe_thread.terminate()
        self.mainframe_thread.wait()

        # Update UI
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")

        self.stop_button.setEnabled(False)
        self.shutdown_button.setEnabled(False)
    def shutdown_system(self):
        print("Sending shutdown command...")
        with open("events_out.jsonl", "a") as f:
            f.write(json.dumps({
                "type": "shutdown",
                "message": "close_all_trades"
            }) + "\n")

        self.stop_mainframe()
    def fetch_equity_value(self):
        try:
            with open("equity.json", "r") as f:
                data = json.load(f)
                return float(data.get("equity", 0))
        except:
            return 0.0
    def start_mainframe(self):
        print("Starting mainframe.py...")
        self.mock_generator.start()
        self.mainframe_thread.start()
        self.listener_thread.running = True
        self.listener_thread.start()

        # Update UI
        self.start_button.setEnabled(False)
        self.start_button.setText("Running...")
        self.stop_button.setEnabled(True)
        self.shutdown_button.setEnabled(True)
        open("mock_events.jsonl", "w").close()
        
    from PySide6.QtCore import QPropertyAnimation, QEasingCurve
    from PySide6.QtGui import QColor

    def flash_equity(self, color):
        anim = QPropertyAnimation(self.equity_label, b"styleSheet")
        anim.setDuration(350)
        anim.setStartValue(f"color: {color}; font-size: 18px; font-weight: bold;")
        anim.setEndValue("color: white; font-size: 18px; font-weight: bold;")
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
    def update_equity(self):
        new_equity = self.fetch_equity_value()

        current_text = self.equity_label.text().replace("Total Equity: $", "").replace(",", "")
        try:
            current_equity = float(current_text)
        except:
            current_equity = new_equity

        self.equity_label.setText(f"Total Equity: ${new_equity:,.2f}")

        if new_equity > current_equity:
            self.flash_equity("#2ecc71")
        elif new_equity < current_equity:
            self.flash_equity("#e74c3c") 
    def add_trade(self, trade_data):
        pass
    def complete_trade(self, trade_data):
        print("DEBUG: complete_trade called with:", trade_data)
        self.trade_history.add_trade(trade_data)

        widget = CompletedTradeWidget(trade_data)
        self.completed_sidebar_layout.insertWidget(
            self.completed_sidebar_layout.count() - 1,
            widget
        )
        self.completed_widgets.append(widget)

        self.completed_scroll.verticalScrollBar().setValue(0)

        self.refresh_all_charts()
    def refresh_all_charts(self):
        trades = self.trade_history.get_all()

        equity = 0
        curve = []
        for t in trades:
            equity += t.get("gain", 0)
            curve.append({
                "date": t.get("timestamp", "N/A"),
                "equity": equity
            })

        self.equity_chart.set_data(curve, trades)
        self.sharpe_chart.set_data(trades)
        self.scatter_chart.set_data(trades)
        with open("equity.json", "w") as f:
            json.dump({"equity": curve[-1]["equity"] if curve else 0}, f)
    def add_trade_widget_to_grid(self, widget):
        index = len(self.trade_widgets)
        row = index // 3
        col = index % 3

        self.trade_grid.addWidget(widget, row, col)
        self.trade_widgets.append(widget)
    def add_trade_ui(self, trade_data):
        box = TradeBox(trade_data)
        box.terminate_signal.connect(self.handle_termination)
        self.add_trade_widget_to_grid(box)
    def handle_termination(self, trade_data):
        for i, widget in enumerate(self.trade_widgets):
            if widget.trade_data == trade_data:
                widget.setParent(None)
                self.trade_widgets.pop(i)
                break

        self.rebuild_grid()

        self.complete_trade(trade_data)
    def rebuild_grid(self):
        for i in reversed(range(self.trade_grid.count())):
            item = self.trade_grid.itemAt(i)
            if item:
                self.trade_grid.removeItem(item)

        for i, widget in enumerate(self.trade_widgets):
            row = i // 3
            col = i % 3
            self.trade_grid.addWidget(widget, row, col)
    def update_trade(self, trade_data):
        for widget in self.trade_widgets:
            if widget.trade_data["id"] == trade_data["id"]:
                widget.update_fields(trade_data)
                break
class MainframeThread(QThread):
    started_signal = Signal()
    finished_signal = Signal()

    def run(self):
        self.started_signal.emit()

        import subprocess
        process = subprocess.Popen(
            ["python", "mainframe.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        process.wait()
        self.finished_signal.emit()
import json
import time
import os
from PySide6.QtCore import QThread
import random
import time
import json
from datetime import datetime, timedelta

class MockEventGenerator(QThread):
    def __init__(self, output_file="mock_events.jsonl"):
        super().__init__()
        self.output_file = output_file
        self.running = True
        self.counter = 1
        self.active_trades = {} 

    def run(self):
        exit_reasons = ["TP Hit", "SL Hit", "Manual Exit", "Time-Based Exit"]

        while self.running:

            if self.counter <= 1 or len(self.active_trades) == 0:
                event_type = "new_trade"
            else:
                event_type = random.choice(["new_trade", "update_trade", "close_trade"])

            # -------------------------
            # NEW TRADE
            # -------------------------
            if event_type == "new_trade":
                symbol = random.choice(["AAPL", "TSLA", "MSFT", "NVDA"])
                entry_price = round(random.uniform(100, 300), 2)

                data = {
                    "id": self.counter,
                    "symbol": symbol,
                    "entry": entry_price,
                    "stop": round(entry_price - random.uniform(5, 20), 2),
                    "tp": round(entry_price + random.uniform(5, 20), 2),
                    "shares": random.randint(1, 20),
                    "exit_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "r_multiple": 0
                }

                self.active_trades[self.counter] = {
                    "symbol": symbol,
                    "open_time": datetime.now()
                }

                self.counter += 1

            elif event_type == "update_trade":
                trade_id = random.choice(list(self.active_trades.keys()))
                symbol = self.active_trades[trade_id]["symbol"]
                entry_price = round(random.uniform(100, 300), 2)

                data = {
                    "id": trade_id,
                    "symbol": symbol,
                    "entry": entry_price,
                    "stop": round(entry_price - random.uniform(5, 20), 2),
                    "tp": round(entry_price + random.uniform(5, 20), 2),
                    "shares": random.randint(1, 20),
                    "exit_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "r_multiple": 0
                }

            else:
                trade_id = random.choice(list(self.active_trades.keys()))
                trade_info = self.active_trades[trade_id]

                symbol = trade_info["symbol"]
                start_time = trade_info["open_time"]
                end_time = datetime.now()

                delta = end_time - start_time
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60

                data = {
                    "id": trade_id,
                    "symbol": symbol,
                    "gain": round(random.uniform(-5, 5), 2),
                    "reason": random.choice(exit_reasons),
                    "duration": f"{hours}h {minutes}m",
                    "timestamp": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "r_multiple": 0
                }

                del self.active_trades[trade_id]
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"type": event_type, "data": data}) + "\n")

            time.sleep(random.uniform(1.0, 3.0))
class TradeEventListener(QThread):
    new_trade_signal = Signal(dict)
    update_trade_signal = Signal(dict)
    close_trade_signal = Signal(dict)

    def __init__(self, event_file="mock_events.jsonl"):
        super().__init__()
        self.event_file = event_file
        self.running = True

    def run(self):
        last_size = 0

        while self.running:
            if os.path.exists(self.event_file):
                size = os.path.getsize(self.event_file)

                if size > last_size:
                    with open(self.event_file, "r") as f:
                        f.seek(last_size)
                        for line in f:
                            try:
                                event = json.loads(line.strip())
                            except json.JSONDecodeError:
                                print("Skipping corrupted JSON line:", line)
                                continue
                            self.handle_event(event)

                    last_size = size

            time.sleep(0.5)

    def handle_event(self, event):
        try:
            etype = event.get("type")
        except:
            print("Skipping invalid event:", event)
            return
        if etype == "new_trade":
            self.new_trade_signal.emit(event["data"])

        elif etype == "update_trade":
            self.update_trade_signal.emit(event["data"])

        elif etype == "close_trade":
            self.close_trade_signal.emit(event["data"])
class CompletedTradeWidget(QFrame):
    def __init__(self, trade_data):
        super().__init__()

        gain = trade_data.get("gain", 0)
        color = "#4caf50" if gain >= 0 else "#e53935"

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #111;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 6px;
            }}
            QLabel {{
                color: white;
                font-size: 12px;
            }}
            .gain {{
                color: {color};
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(2)

        symbol = QLabel(f"{trade_data['symbol']}")
        pl = QLabel(f"{gain:+.2f}%")
        pl.setObjectName("gain")
        pl.setProperty("class", "gain")

        reason_text = trade_data.get("reason", "Unknown")
        reason = QLabel(f"Exit: {reason_text}")
        duration_text = trade_data.get("duration", "N/A")
        duration = QLabel(f"Duration: {duration_text}")
        timestamp_text = trade_data.get("timestamp", "N/A")
        timestamp = QLabel(f"Timestamp: {timestamp_text}")

        layout.addWidget(symbol)
        layout.addWidget(pl)
        layout.addWidget(reason)
        layout.addWidget(duration)
        layout.addWidget(timestamp)

        self.setLayout(layout)
class TradeBox(QFrame):
    terminate_signal = Signal(dict)  # emits trade data when terminated

    def __init__(self, trade_data):
        super().__init__()

        self.trade_data = trade_data

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            QPushButton {
                background-color: #aa3333;
                color: white;
                border-radius: 5px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #cc4444;
            }
        """)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.setSpacing(6)

        self.symbol = QLabel(f"Symbol: {trade_data['symbol']}")
        self.entry = QLabel(f"Entry: {trade_data['entry']}")
        self.stop = QLabel(f"Stoploss: {trade_data['stop']}")
        self.tp = QLabel(f"Take Profit: {trade_data['tp']}")
        self.shares = QLabel(f"Shares: {trade_data['shares']}")

        self.terminate_btn = QPushButton("Terminate")
        self.terminate_btn.clicked.connect(self.terminate_trade)

        layout.addWidget(self.symbol)
        layout.addWidget(self.entry)
        layout.addWidget(self.stop)
        layout.addWidget(self.tp)
        layout.addWidget(self.shares)
        layout.addWidget(self.terminate_btn)

        self.setLayout(layout)

    def terminate_trade(self):
        self.terminate_signal.emit(self.trade_data)

        with open("events_out.jsonl", "a") as f:
            f.write(json.dumps({
                "type": "terminate",
                "id": self.trade_data["id"]
            }) + "\n")
    def update_fields(self, data):
        self.entry.setText(f"Entry: {data['entry']}")
        self.stop.setText(f"Stoploss: {data['stop']}")
        self.tp.setText(f"Take Profit: {data['tp']}")
        self.shares.setText(f"Shares: {data['shares']}")

# -----------------------------
# Equity + Drawdown Chart
# -----------------------------
class EquityChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = MplCanvas(width=6, height=4, dpi=100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.equity_curve = []
        self.trades = []
        self.hover_idx = None

        # Enable mouse tracking for hover
        self.setMouseTracking(True)
        self.canvas.setMouseTracking(True)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("figure_leave_event", self.on_mouse_leave)
        # --- Tooltip for trade hover ---
        self.tooltip = QLabel(self)
        self.tooltip.setStyleSheet(
            f"""
            background-color: {C['panel']};
            color: {C['bright']};
            border: 1px solid {C['border']};
            padding: 4px 6px;
            border-radius: 4px;
            font-family: 'Menlo';
            font-size: 10px;
            """
        )
        self.tooltip.hide()
        self.tooltip_locked = False
        self.locked_idx = None
        self.canvas.mpl_connect("button_press_event", self.on_mouse_click)
    def on_mouse_click(self, event):
        if event.inaxes is None:
            return

        # Convert click to nearest index
        x = int(round(event.xdata))
        if x < 0 or x >= len(self.equity_curve):
            return

        trade = self.find_trade_at_index(x)

        # --- CASE 1: Clicking a trade dot ---
        if trade:
            # If already locked on THIS dot → unlock
            if self.tooltip_locked and self.locked_idx == x:
                self.tooltip_locked = False
                self.locked_idx = None
                self.tooltip.hide()
            else:
                # Lock on this new dot
                self.tooltip_locked = True
                self.locked_idx = x
                self.show_trade_tooltip(event, x, trade)

            self.redraw()
            return

        # --- CASE 2: Clicking anywhere else → unlock ---
        self.tooltip_locked = False
        self.locked_idx = None
        self.tooltip.hide()
        self.redraw()
    def find_trade_at_index(self, idx):
        for t in self.trades:
            exit_dt = t.get("exit_dt")
            if exit_dt is None:
                continue  # skip incomplete trades

            eq_idx = next(
                (i for i, e in enumerate(self.equity_curve)
                if e["date"] >= exit_dt),
                None
            )

            if eq_idx == idx:
                return t

        return None
    def set_data(self, equity_curve, trades):
        self.equity_curve = equity_curve or []
        self.trades = trades or []
        self.hover_idx = None
        self.redraw()

    def on_mouse_move(self, event):
        if self.tooltip_locked:
            return
        if not self.equity_curve or event.xdata is None:
            return
        x = int(round(event.xdata))
        x = max(0, min(len(self.equity_curve) - 1, x))
        if x != self.hover_idx:
            self.hover_idx = x
            self.redraw()
        # Show tooltip if hovering over a trade dot
        # --- Tooltip on trade hover ---
        trade = self.find_trade_at_index(self.hover_idx)
        if trade:
            self.show_trade_tooltip(event, self.hover_idx, trade)
        else:
            self.tooltip.hide()

    def on_mouse_leave(self, event):
        if self.hover_idx is not None:
            self.hover_idx = None
            self.redraw()
        self.tooltip.hide()
    def show_trade_tooltip(self, event, idx, trade):
        eq_val = self.equity_curve[idx]["equity"]
        pnl = trade["realised_pnl"]
        r = trade["r_multiple"]
        sector = trade["sector"]
        reason = trade.get("exit_reason", "N/A")
        symbol = trade["symbol"]
        date = trade["exit_dt"]

        self.tooltip.setText(
            f"{symbol}  ({sector})\n"
            f"Date: {date}\n"
            f"Equity: ${eq_val:,.0f}\n"
            f"PnL: {'+' if pnl>=0 else ''}${pnl:,.0f}\n"
            f"R: {r:+.2f}R\n"
            f"Exit: {reason}"
        )

        self.tooltip.adjustSize()

        # Convert Matplotlib coords → Qt coords
        qt_x = int(event.guiEvent.position().x()) + 20
        qt_y = int(event.guiEvent.position().y()) + 20

        # Clamp inside widget
        qt_x = min(qt_x, self.width() - self.tooltip.width() - 10)
        qt_y = min(qt_y, self.height() - self.tooltip.height() - 10)

        self.tooltip.move(qt_x, qt_y)
        self.tooltip.show()
    def redraw(self):
        self.canvas.clear()
        fig = self.canvas.fig

        if not self.equity_curve:
            self.canvas.draw()
            return

        eq_vals = np.array([p["equity"] for p in self.equity_curve])
        dates = [p["date"] for p in self.equity_curve]
        N = len(eq_vals)
        x = np.arange(N)

        # --- Two axes: equity (left) and drawdown (right) ---
        ax_eq = fig.add_subplot(111)
        ax_eq.set_facecolor(C["surface"])
        ax_dd = ax_eq.twinx()

        # -------------------------
        # Drawdown series
        # -------------------------
        peaks = np.maximum.accumulate(eq_vals)
        dd_series = (peaks - eq_vals) / peaks

        # -------------------------
        # Equity fill + line
        # -------------------------
        eq_min = eq_vals.min() * 0.995
        ax_eq.fill_between(x, eq_vals, eq_min, color=rgba(0, 200, 180, 0.22))
        ax_eq.plot(x, eq_vals, color=C["teal"], linewidth=1.5)

        # -------------------------
        # Drawdown fill + line
        # -------------------------
        ax_dd.fill_between(x, -dd_series, 0, color=rgba(220, 40, 60, 0.45))
        ax_dd.plot(x, -dd_series, color=C["red"], linewidth=1.0)

        # -------------------------
        # Trade dots (FIXED)
        # -------------------------
        for t in self.trades:
            exit_dt = t.get("exit_dt")
            if exit_dt is None:
                continue  # skip incomplete trades

            idx = next(
                (i for i, e in enumerate(self.equity_curve)
                if e["date"] >= exit_dt),
                None
            )

            if idx is None:
                continue

            color = C["green"] if t["realised_pnl"] >= 0 else C["red"]

            # Draw dots on the EQUITY axis
            ax_eq.scatter(idx, eq_vals[idx], s=28, color=color, zorder=6)

        # -------------------------
        # Y-axis labels
        # -------------------------
        yticks = np.linspace(eq_min, eq_vals.max() * 1.005, 5)
        ax_eq.set_yticks(yticks)
        ax_eq.set_yticklabels([f"${int(v/1000)}k" for v in yticks], color=C["muted"])

        ax_dd.set_ylabel("Drawdown", color=C["muted"])
        ax_dd.tick_params(axis="y", colors=C["muted"])
        # -------------------------
        # Find nearest trade logic
        # -------------------------
        def find_trade_at_index(self, idx):
            for t in self.trades:
                exit_dt = t.get("exit_dt")
                if exit_dt is None:
                    continue  # skip incomplete trades

                eq_idx = next(
                    (i for i, e in enumerate(self.equity_curve)
                    if e["date"] >= exit_dt),
                    None
                )

                if eq_idx == idx:
                    return t

            return None

        # -------------------------
        # X-axis labels
        # -------------------------
        step = max(1, N // 7)
        ax_eq.set_xticks(x[::step])
        ax_eq.set_xticklabels([d[:7] for d in dates[::step]], color=C["muted"])

        # -------------------------
        # Hover crosshair
        # -------------------------
        highlight_idx = self.locked_idx if self.tooltip_locked else self.hover_idx
        if highlight_idx is not None:
            ax_eq.axvline(highlight_idx, color=rgba(184,200,208,0.25),
                        linestyle="--", linewidth=0.7)
            ax_eq.scatter(highlight_idx, eq_vals[highlight_idx],
                        s=40, color=C["teal2"], zorder=7)

        # -------------------------
        # Styling
        # -------------------------
        for spine in ax_eq.spines.values():
            spine.set_color(C["border"])
        for spine in ax_dd.spines.values():
            spine.set_color(C["border"])

        ax_eq.set_title("Equity & Drawdown", color=C["teal"], loc="left")
        ax_eq.tick_params(colors=C["muted"])

        self.canvas.draw()


# -----------------------------
# Rolling Sharpe Chart
# -----------------------------
class SharpeChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = MplCanvas(width=6, height=3.5, dpi=100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.trades = []

    def set_data(self, trades):
        self.trades = trades or []
        self.redraw()

    def compute_series(self, window=20):
        trades = self.trades
        if len(trades) < window:
            return []

        series = []
        for i in range(window, len(trades) + 1):
            slice_ = trades[i - window:i]
            rs = [t["realised_pnl"] for t in slice_]
            mean = np.mean(rs)
            std = np.std(rs, ddof=1)
            sharpe = (mean / std) * math.sqrt(252 / window) if std > 0 else 0
            series.append({
                "x": i,
                "sharpe": sharpe,
                "date": trades[i - 1]["exit_dt"]
            })
        return series

    def redraw(self):
        ax = self.canvas.ax
        self.canvas.clear()
        ax = self.canvas.ax

        series = self.compute_series()
        if not series:
            self.canvas.draw()
            return

        xs = np.arange(len(series))
        vals = np.array([s["sharpe"] for s in series])
        dates = [s["date"] for s in series]

        y_min = min(vals.min(), -0.5) * 1.1
        y_max = max(vals.max(), 0.5) * 1.1

        # Zero line
        ax.axhline(0, color=C["border2"], linewidth=1)

        # Fill above/below zero
        for i in range(1, len(vals)):
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = vals[i - 1], vals[i]
            poly = Polygon(
                [(x0, 0), (x0, y0), (x1, y1), (x1, 0)],
                closed=True,
                color=rgba(0, 200, 180, 0.15) if vals[i] >= 0 else rgba(220, 40, 60, 0.15)
            )
            ax.add_patch(poly)

        # Line
        ax.plot(xs, vals, color=C["teal"], linewidth=1.5)

        # Y labels
        ax.set_yticks([y_min, 0, y_max])
        ax.set_yticklabels([f"{v:.1f}" for v in [y_min, 0, y_max]], color=C["muted"])

        # X labels
        step = max(1, len(xs) // 5)
        ax.set_xticks(xs[::step])
        ax.set_xticklabels([d[:7] for d in dates[::step]], color=C["muted"])

        ax.set_title("Rolling Sharpe (20‑trade)", color=C["amber"], loc="left")
        ax.spines["top"].set_color(C["border"])
        ax.spines["right"].set_color(C["border"])
        ax.spines["bottom"].set_color(C["border"])
        ax.spines["left"].set_color(C["border"])
        ax.tick_params(colors=C["muted"])

        self.canvas.draw()


# -----------------------------
# R‑Multiple Scatter Chart
# -----------------------------
class ScatterChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = MplCanvas(width=6, height=3.5, dpi=100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.trades = []
        self.tooltip = QLabel(self)
        self.tooltip.setStyleSheet(
            f"""
            background-color: {C['panel']};
            color: {C['bright']};
            border: 1px solid {C['border']};
            padding: 10px 14px;
            border-radius: 6px;
            font-family: 'Menlo';
            font-size: 16px;
            """
        )
        self.tooltip.hide()

        self.tooltip_locked = False
        self.locked_idx = None
        self.hover_idx = None
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("figure_leave_event", self.on_mouse_leave)
        self.canvas.mpl_connect("button_press_event", self.on_mouse_click)
    def find_trade_at_index(self, idx):
        if idx < 0 or idx >= len(self.trades):
            return None
        return self.trades[idx]
    def show_trade_tooltip(self, event, idx, trade):
        pnl = trade["realised_pnl"]
        r = trade["r_multiple"]
        sector = trade["sector"]
        reason = trade.get("exit_reason", "N/A")
        symbol = trade["symbol"]
        date = trade["exit_dt"]

        self.tooltip.setText(
            f"{symbol}  ({sector})\n"
            f"Date: {date}\n"
            f"PnL: {'+' if pnl>=0 else ''}${pnl:,.0f}\n"
            f"R-Multiple: {r:+.2f}R\n"
            f"Exit: {reason}"
        )

        self.tooltip.adjustSize()

        # Convert Matplotlib coords → Qt coords
        qt_x = int(event.guiEvent.position().x()) + 20
        qt_y = int(event.guiEvent.position().y()) + 20

        # Clamp inside widget
        qt_x = min(qt_x, self.width() - self.tooltip.width() - 10)
        qt_y = min(qt_y, self.height() - self.tooltip.height() - 10)

        self.tooltip.move(qt_x, qt_y)
        self.tooltip.show()
    def on_mouse_move(self, event):
        if self.tooltip_locked:
            return

        if event.inaxes is None:
            self.tooltip.hide()
            return

        if event.xdata is None:
            self.tooltip.hide()
            return

        idx = int(round(event.xdata))
        self.hover_idx = idx

        trade = self.find_trade_at_index(idx)
        if trade:
            self.show_trade_tooltip(event, idx, trade)
        else:
            self.tooltip.hide()

        self.redraw()
    def on_mouse_leave(self, event):
        if not self.tooltip_locked:
            self.tooltip.hide()
            self.hover_idx = None
            self.redraw()
    def on_mouse_click(self, event):
        if event.inaxes is None:
            return

        if event.xdata is None:
            return

        idx = int(round(event.xdata))
        trade = self.find_trade_at_index(idx)

        # Clicking a trade dot
        if trade:
            # Clicking the same locked dot → unlock
            if self.tooltip_locked and self.locked_idx == idx:
                self.tooltip_locked = False
                self.locked_idx = None
                self.tooltip.hide()
            else:
                # Lock on this dot
                self.tooltip_locked = True
                self.locked_idx = idx
                self.show_trade_tooltip(event, idx, trade)

            self.redraw()
            return

        # Clicking empty space → unlock
        self.tooltip_locked = False
        self.locked_idx = None
        self.tooltip.hide()
        self.redraw()
    def set_data(self, trades):
        self.trades = trades or []
        self.redraw()

    def redraw(self):
        ax = self.canvas.ax
        self.canvas.clear()
        ax = self.canvas.ax

        trades = self.trades
        if not trades:
            self.canvas.draw()
            return

        rs = np.array([t["r_multiple"] for t in trades if "r_multiple" in t])
        r_min = min(rs.min(), -3) - 0.2
        r_max = max(rs.max(), 3) + 0.2
        N = len(trades)
        xs = np.arange(N)

        # Expectancy line
        mean_r = rs.mean()
        ax.axhline(mean_r, linestyle="--", linewidth=0.8,
                   color=rgba(232, 160, 48, 0.5))
        ax.text(0.01, 0.95, f"avg R={mean_r:.2f}",
                transform=ax.transAxes, color=C["amber"], fontsize=8,
                va="top")

        # Scatter dots
        for i, t in enumerate(trades):
            sector = t.get("sector")
            if sector is None:
                continue  # skip incomplete trades

            col = C["sector"].get(sector, C["muted"])
            ax.scatter(i, t["r_multiple"], s=25, color=col, alpha=0.75)

        # Y labels
        yticks = [math.ceil(r_min), 0, math.floor(r_max)]
        ax.set_yticks(yticks)
        ax.set_yticklabels([f"{v}R" for v in yticks], color=C["muted"])

        ax.set_title("R‑Multiple per Trade", color=C["bright"], loc="left")
        ax.set_xlabel("Trade index", color=C["muted"])

        ax.set_ylim(r_min, r_max)
        ax.spines["top"].set_color(C["border"])
        ax.spines["right"].set_color(C["border"])
        ax.spines["bottom"].set_color(C["border"])
        ax.spines["left"].set_color(C["border"])
        ax.tick_params(colors=C["muted"])

        self.canvas.draw()
        highlight_idx = self.locked_idx if self.tooltip_locked else self.hover_idx
        if highlight_idx is not None and 0 <= highlight_idx < len(self.trades):
            r = self.trades[highlight_idx]["r_multiple"]
            ax.scatter(highlight_idx, r, s=80, color=C["teal2"], zorder=6)
# ------------------------------------------------------------
# Sector Bars Widget
# ------------------------------------------------------------
class SectorBarsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.by_sector = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("SECTOR P&L")
        title.setFont(MONO)
        title.setStyleSheet(f"color:{C['muted']}; letter-spacing:2px; font-size:10px;")
        layout.addWidget(title)

        self.container = QVBoxLayout()
        layout.addLayout(self.container)

    def set_data(self, by_sector):
        self.by_sector = by_sector or {}
        self.refresh()

    def refresh(self):
        # Clear old widgets
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = [(sec, v) for sec, v in self.by_sector.items() if v["trades"] > 0]
        if not entries:
            return

        max_abs = max(abs(v["net_pnl"]) for _, v in entries)

        for sec, v in entries:
            col = C["sector"].get(sec, C["muted"])
            pnl = v["net_pnl"]
            pct = abs(pnl) / max_abs if max_abs > 0 else 0

            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 6, 6)
            row_layout.setSpacing(2)

            # Header row
            top = QHBoxLayout()
            lbl_sec = QLabel(sec.upper())
            lbl_sec.setFont(MONO)
            lbl_sec.setStyleSheet(f"color:{col}; font-size:10px;")

            lbl_pnl = QLabel(f"{'+' if pnl>=0 else ''}${int(pnl):,}")
            lbl_pnl.setFont(MONO)
            lbl_pnl.setStyleSheet(f"color:{C['green'] if pnl>=0 else C['red']}; font-size:10px;")

            top.addWidget(lbl_sec)
            top.addStretch()
            top.addWidget(lbl_pnl)
            row_layout.addLayout(top)

            # Bar
            bar_bg = QFrame()
            bar_bg.setStyleSheet(f"background:{C['border']}; border-radius:2px;")
            bar_bg.setFixedHeight(4)

            bar_fg = QFrame(bar_bg)
            bar_fg.setStyleSheet(
                f"background:{col if pnl>=0 else C['red']}; border-radius:2px;"
            )
            bar_fg.setGeometry(0, 0, int(pct * 180), 4)

            row_layout.addWidget(bar_bg)

            # Stats row
            stats = QLabel(
                f"{v['trades']} trades   WR {v['win_rate']:.0f}%   avgR {v['avg_r']:+.2f}R"
            )
            stats.setFont(MONO)
            stats.setStyleSheet(f"color:{C['muted']}; font-size:9px;")
            row_layout.addWidget(stats)

            self.container.addWidget(row)


# ------------------------------------------------------------
# Exit Reasons Widget
# ------------------------------------------------------------
class ExitReasonsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("EXIT REASONS")
        title.setFont(MONO)
        title.setStyleSheet(f"color:{C['muted']}; letter-spacing:2px; font-size:10px;")
        layout.addWidget(title)

        self.container = QVBoxLayout()
        layout.addLayout(self.container)

    def set_data(self, close_reasons):
        self.data = close_reasons or {}
        self.refresh()

    def refresh(self):
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for reason, count in self.data.items():
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)

            lbl_r = QLabel(reason.replace("_", " "))
            lbl_r.setFont(MONO)
            lbl_r.setStyleSheet(f"color:{C['reason'].get(reason, C['muted'])}; font-size:10px;")

            lbl_n = QLabel(str(count))
            lbl_n.setFont(MONO)
            lbl_n.setStyleSheet(f"color:{C['bright']}; font-size:10px;")

            h.addWidget(lbl_r)
            h.addStretch()
            h.addWidget(lbl_n)

            self.container.addWidget(row)


# ------------------------------------------------------------
# Sector Legend Widget
# ------------------------------------------------------------
class SectorLegendWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("SECTOR COLOUR")
        title.setFont(MONO)
        title.setStyleSheet(f"color:{C['muted']}; letter-spacing:2px; font-size:10px;")
        layout.addWidget(title)

        for sec, col in C["sector"].items():
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)

            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{col}; border-radius:5px;")

            lbl = QLabel(sec.upper())
            lbl.setFont(MONO)
            lbl.setStyleSheet(f"color:{C['muted']}; font-size:10px;")

            h.addWidget(dot)
            h.addWidget(lbl)
            layout.addWidget(row)


# ------------------------------------------------------------
# Recent Trades Widget
# ------------------------------------------------------------
class RecentTradesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trades = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("RECENT TRADES")
        title.setFont(MONO)
        title.setStyleSheet(f"color:{C['muted']}; letter-spacing:2px; font-size:10px;")
        layout.addWidget(title)

        self.container = QVBoxLayout()
        layout.addLayout(self.container)

    def set_data(self, trades):
        self.trades = trades or []
        self.refresh()

    def refresh(self):
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = self.trades[-8:][::-1]

        for t in recent:
            row = QWidget()
            v = QVBoxLayout(row)
            v.setContentsMargins(0, 0, 0, 6)
            v.setSpacing(2)

            # Top row
            top = QHBoxLayout()
            lbl_sym = QLabel(t["symbol"])
            lbl_sym.setFont(MONO)
            lbl_sym.setStyleSheet(
                f"color:{C['sector'].get(t['sector'], C['muted'])}; font-size:11px; font-weight:600;"
            )

            pnl = t["realised_pnl"]
            lbl_pnl = QLabel(f"{'+' if pnl>=0 else ''}${int(pnl):,}")
            lbl_pnl.setFont(MONO)
            lbl_pnl.setStyleSheet(f"color:{C['green'] if pnl>=0 else C['red']}; font-size:11px;")

            top.addWidget(lbl_sym)
            top.addStretch()
            top.addWidget(lbl_pnl)
            v.addLayout(top)

            # Bottom row
            bot = QHBoxLayout()
            lbl_dt = QLabel(t.get("exit_dt"))
            lbl_dt.setFont(MONO)
            lbl_dt.setStyleSheet(f"color:{C['muted']}; font-size:9px;")

            r = t["r_multiple"]
            lbl_r = QLabel(f"{'+' if r>=0 else ''}{r}R")
            lbl_r.setFont(MONO)
            lbl_r.setStyleSheet(f"color:{C['teal'] if r>=0 else C['red']}; font-size:9px;")

            bot.addWidget(lbl_dt)
            bot.addStretch()
            bot.addWidget(lbl_r)
            v.addLayout(bot)

            # Divider
            div = QFrame()
            div.setFrameShape(QFrame.HLine)
            div.setStyleSheet(f"color:{C['border']};")
            v.addWidget(div)

            self.container.addWidget(row)


# ------------------------------------------------------------
# Collapsible Sidebar (TradingView-style)
# ------------------------------------------------------------
class CollapsibleSidebar(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Sidebar", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        # Container widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Collapse button
        self.btn = QPushButton("⮜")
        self.btn.setFixedHeight(24)
        self.btn.setStyleSheet(
            f"background:{C['panel']}; color:{C['bright']}; border:1px solid {C['border']};"
        )
        self.btn.clicked.connect(self.toggle)

        self.layout.addWidget(self.btn)
        # Hover effect
        self.tooltip = QLabel(self)
        self.tooltip.setStyleSheet(
            f"""
            background-color: {C['panel']};
            color: {C['bright']};
            border: 1px solid {C['border']};
            padding: 4px 6px;
            border-radius: 4px;
            font-family: 'Menlo';
            font-size: 10px;
            """
        )
        self.tooltip.hide()

        # Scroll area for widgets
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background:{C['surface']}; border:none;")
        self.layout.addWidget(self.scroll)

        self.inner = QWidget()
        self.scroll.setWidget(self.inner)
        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(12)

        # Widgets
        self.w_sector = SectorBarsWidget()
        self.w_exit = ExitReasonsWidget()
        self.w_legend = SectorLegendWidget()
        self.w_recent = RecentTradesWidget()

        self.inner_layout.addWidget(self.w_sector)
        self.inner_layout.addWidget(self.w_exit)
        self.inner_layout.addWidget(self.w_legend)
        self.inner_layout.addWidget(self.w_recent)
        self.inner_layout.addStretch()

        # Animation
        self.is_collapsed = False
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(250)  # 250ms (your choice)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.full_width = 260
        self.setFixedWidth(self.full_width)
        self.collapsed_width = 28
        self.setMaximumWidth(self.full_width)

    def toggle(self):
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self):
        self.is_collapsed = True
        self.btn.setText("⮞")
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.collapsed_width)
        self.animation.start()

    def expand(self):
        self.is_collapsed = False
        self.btn.setText("⮜")
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.full_width)
        self.animation.start()

    def auto_collapse_if_needed(self, window_width):
        """Auto-collapse when window is narrow."""
        if window_width < 900 and not self.is_collapsed:
            self.collapse()
        elif window_width >= 900 and self.is_collapsed:
            self.expand()

    def set_data(self, data):
        self.w_sector.set_data(data.get("by_sector"))
        self.w_exit.set_data(data.get("close_reasons"))
        self.w_recent.set_data(data.get("trades"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chimera Backtest Visualiser")
        self.resize(1400, 900)
        self.setStyleSheet(f"background:{C['bg']}; color:{C['text']};")
        self.brand_label = QLabel("Chimera")
        self.brand_label.setStyleSheet("""
            color: #D4AF37;          /* gold */
            font-size: 22px;
            font-weight: 600;
            padding-left: 12px;
        """)

        # -----------------------------
        # Central widget (tabs + charts)
        # -----------------------------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {C['border']};
                background: {C['surface']};
            }}
            QTabBar::tab {{
                background: {C['panel']};
                color: {C['muted']};
                padding: 6px 14px;
                font-family: 'Menlo';
                font-size: 10px;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background: {C['surface']};
                color: {C['teal']};
                border-bottom: 2px solid {C['teal']};
            }}
            """
        )
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        from about_tab import AboutTab
        # Chart widgets
        self.w_equity = EquityChartWidget()
        self.w_sharpe = SharpeChartWidget()
        self.w_scatter = ScatterChartWidget()
        self.w_control = BuyingTab()

        self.w_control.attach_charts(
            self.w_equity,
            self.w_sharpe,
            self.w_scatter
        )

        self.w_control.rebuild_from_history()
        self.w_control.refresh_all_charts()

        self.tabs.addTab(self.w_control, "Controls")
        self.tabs.addTab(self.w_equity, "Equity + Drawdown")
        self.tabs.addTab(self.w_sharpe, "Rolling Sharpe")
        self.tabs.addTab(self.w_scatter, "R‑Multiple Scatter")
        self.tabs.addTab(AboutTab(), "About")

        top_area = QVBoxLayout()
        top_area.setContentsMargins(0, 0, 0, 0)
        top_area.setSpacing(0)

        # Add Chimera label (aligned left)
        tab_height = self.tabs.tabBar().height()
        padding = max(0, (tab_height // 2) - 10)  # tweak the -10 offset
        self.brand_label.setStyleSheet(f"""
            color: #D4AF37;
            font-size: 22px;
            font-weight: 600;
            padding-left: 12px;
            padding-top: {padding}px;
            background: transparent;
        """)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(28)              # softness of glow
        glow.setOffset(0, 0)                # centered glow
        glow.setColor(QColor(212, 175, 55, 180))  # gold glow
        self.brand_label.setGraphicsEffect(glow)
        self.brand_label.setGraphicsEffect(glow)
        self.brand_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_area.addWidget(self.brand_label)

        # Add tabs below it
        top_area.addWidget(self.tabs)

        # Wrap in container
        container = QWidget()
        container.setLayout(top_area)

        self.setCentralWidget(container)

        # -----------------------------
        # Sidebar (collapsible)
        # -----------------------------
        self.sidebar = CollapsibleSidebar(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.sidebar)

        # -----------------------------
        # Menu bar (Load JSON)
        # -----------------------------
        load_action = QAction("Load JSON", self)
        load_action.triggered.connect(self.load_json_dialog)

        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(load_action)

    # --------------------------------------------------------
    # Load JSON file
    # --------------------------------------------------------
    def load_json_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Backtest JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.set_data(data)
        except Exception as e:
            print("Failed to load JSON:", e)
    def set_data(self, data):
        self.data = data

        eq = data.get("equity_curve", [])
        trades = data.get("trades", [])

        # Update charts
        self.w_equity.set_data(eq, trades)
        self.w_sharpe.set_data(trades)
        self.w_scatter.set_data(trades)

        self.sidebar.set_data(data)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sidebar.auto_collapse_if_needed(self.width())

def run_app():
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
