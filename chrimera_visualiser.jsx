import { useState, useEffect, useRef, useMemo, useCallback } from "react";

/* ─── Demo data generator ─────────────────────────────────────────────────── */
function genDemo() {
  const trades = [];
  const equity = [];
  const sectors = ["stocks","crypto","forex","futures"];
  const symbols = { stocks:["GME","AMC","TSLA","BBBY"], crypto:["BTC/USD","ETH/USD","SOL/USD"], forex:["EUR/USD","GBP/USD"], futures:["ES1!","NQ1!"] };
  const reasons = ["TP_HIT","TRAILING_STOP","STOP_HIT"];

  let eq = 100000, dt = new Date("2022-01-03");
  const step = () => { dt = new Date(dt); dt.setDate(dt.getDate() + 1); return dt.toISOString().slice(0,10); };

  for (let i = 0; i < 380; i++) {
    const d = step();
    const drift = (Math.random() - 0.38) * 0.004;
    eq = Math.max(eq * (1 + drift), 60000);
    equity.push({ date: d, equity: Math.round(eq * 100) / 100 });

    if (i > 0 && Math.random() < 0.22) {
      const sec = sectors[Math.floor(Math.random() * sectors.length)];
      const syms = symbols[sec];
      const sym  = syms[Math.floor(Math.random() * syms.length)];
      const side = Math.random() > 0.35 ? "buy" : "sell";
      const r    = (Math.random() - 0.35) * 3.8;
      const pnl  = r * eq * 0.008;
      const reason = r > 0 ? (Math.random() > 0.4 ? "TP_HIT" : "TRAILING_STOP") : "STOP_HIT";
      trades.push({
        symbol: sym, sector: sec, side,
        realised_pnl: Math.round(pnl * 100) / 100,
        r_multiple: Math.round(r * 100) / 100,
        close_reason: reason,
        exit_dt: d,
        entry_price: 100 + Math.random() * 400,
        exit_price:  100 + Math.random() * 400,
        kelly_fraction: 0.05 + Math.random() * 0.18,
      });
    }
  }

  const pnls = trades.map(t => t.realised_pnl);
  const wins  = pnls.filter(p => p > 0);
  const losses= pnls.filter(p => p <= 0);
  const rs    = trades.map(t => t.r_multiple);
  const finalEq = equity[equity.length - 1].equity;

  // compute max drawdown
  let peak = 0, maxDD = 0;
  for (const { equity: e } of equity) {
    if (e > peak) peak = e;
    const dd = (peak - e) / peak;
    if (dd > maxDD) maxDD = dd;
  }

  return {
    equity_curve: equity,
    trades,
    total_trades:   trades.length,
    win_rate:       Math.round(wins.length / trades.length * 1000) / 1000,
    profit_factor:  Math.round(wins.reduce((a,b)=>a+b,0) / Math.abs(losses.reduce((a,b)=>a+b,0)) * 1000) / 1000,
    net_profit:     Math.round((finalEq - 100000) * 100) / 100,
    total_return_pct: Math.round((finalEq / 100000 - 1) * 10000) / 100,
    cagr_pct:       Math.round((Math.pow(finalEq / 100000, 1 / (380 / 365.25)) - 1) * 10000) / 100,
    max_drawdown_pct: Math.round(maxDD * 10000) / 100,
    sharpe_ratio:   Math.round((0.8 + Math.random() * 0.8) * 1000) / 1000,
    sortino_ratio:  Math.round((1.1 + Math.random() * 1.0) * 1000) / 1000,
    calmar_ratio:   Math.round((0.6 + Math.random() * 0.6) * 1000) / 1000,
    avg_r:          Math.round(rs.reduce((a,b)=>a+b,0) / rs.length * 1000) / 1000,
    expectancy_r:   Math.round((0.2 + Math.random() * 0.3) * 1000) / 1000,
    initial_equity: 100000,
    final_equity:   finalEq,
    backtest_days:  380,
    by_sector: Object.fromEntries(sectors.map(s => {
      const st = trades.filter(t => t.sector === s);
      const sw = st.filter(t => t.realised_pnl > 0);
      return [s, { trades: st.length, win_rate: st.length ? Math.round(sw.length/st.length*100)/100 : 0,
        avg_r: st.length ? Math.round(st.reduce((a,t)=>a+t.r_multiple,0)/st.length*100)/100 : 0,
        net_pnl: Math.round(st.reduce((a,t)=>a+t.realised_pnl,0)*100)/100 }];
    })),
    close_reasons: Object.fromEntries(reasons.map(r => [r, trades.filter(t=>t.close_reason===r).length])),
  };
}

/* ─── Colour palette ──────────────────────────────────────────────────────── */
const C = {
  bg:      "#080a0b",
  surface: "#0e1214",
  panel:   "#131719",
  border:  "#1e2428",
  border2: "#263036",
  dim:     "#3a444a",
  muted:   "#5a6870",
  text:    "#b8c8d0",
  bright:  "#ddeef5",
  teal:    "#00c8b4",
  teal2:   "#00e6ce",
  tealFill:"rgba(0,200,180,0.12)",
  red:     "#e03050",
  redFill: "rgba(220,40,60,0.18)",
  amber:   "#e8a030",
  green:   "#38c870",
  blue:    "#3888e8",
  purple:  "#9060e8",
  sector: { stocks:"#3888e8", crypto:"#9060e8", forex:"#e8a030", futures:"#e03878" },
  reason: { TP_HIT:"#38c870", TRAILING_STOP:"#e8a030", STOP_HIT:"#e03050" },
};

const MONO = "'IBM Plex Mono', 'Courier New', monospace";
const SANS = "'IBM Plex Sans', system-ui, sans-serif";

/* ─── Mini stat card ──────────────────────────────────────────────────────── */
function Stat({ label, value, sub, color }) {
  return (
    <div style={{ padding:"10px 14px", borderRight:`1px solid ${C.border}` }}>
      <div style={{ fontSize:8, color:C.muted, letterSpacing:"0.14em", textTransform:"uppercase", marginBottom:3, fontFamily:MONO }}>{label}</div>
      <div style={{ fontSize:17, fontWeight:500, color: color || C.bright, fontFamily:MONO, lineHeight:1 }}>{value}</div>
      {sub && <div style={{ fontSize:9, color:C.muted, marginTop:2, fontFamily:MONO }}>{sub}</div>}
    </div>
  );
}

/* ─── Canvas chart helpers ────────────────────────────────────────────────── */
function useCanvas(draw, deps) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    c.width  = c.offsetWidth  * dpr;
    c.height = c.offsetHeight * dpr;
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    draw(ctx, c.offsetWidth, c.offsetHeight);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return ref;
}

function drawGrid(ctx, w, h, pad, yMin, yMax, xCount, yCount = 5) {
  ctx.strokeStyle = C.border;
  ctx.lineWidth   = 0.5;
  for (let i = 0; i <= yCount; i++) {
    const y = pad.top + (h - pad.top - pad.bottom) * i / yCount;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
  }
  const step = Math.max(1, Math.floor(xCount / 8));
  for (let i = 0; i < xCount; i += step) {
    const x = pad.left + (w - pad.left - pad.right) * i / (xCount - 1);
    ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, h - pad.bottom); ctx.stroke();
  }
}

/* ─── Equity + drawdown chart ─────────────────────────────────────────────── */
function EquityChart({ equityCurve, trades, hoverIdx, setHoverIdx }) {
  const pad = { top:20, right:16, bottom:36, left:72 };

  const { eqMin, eqMax, ddSeries } = useMemo(() => {
    if (!equityCurve.length) return { eqMin:0, eqMax:1, ddSeries:[] };
    const vals = equityCurve.map(p => p.equity);
    let peak = vals[0], dd = [];
    for (const v of vals) {
      if (v > peak) peak = v;
      dd.push(peak > 0 ? (peak - v) / peak : 0);
    }
    return { eqMin: Math.min(...vals) * 0.995, eqMax: Math.max(...vals) * 1.005, ddSeries: dd };
  }, [equityCurve]);

  const draw = useCallback((ctx, w, h) => {
    if (!equityCurve.length) return;
    const N   = equityCurve.length;
    const cw  = w - pad.left - pad.right;
    const ch  = h - pad.top  - pad.bottom;
    const ddH = Math.floor(ch * 0.22);
    const eqH = ch - ddH - 8;

    ctx.clearRect(0, 0, w, h);

    const xOf = i => pad.left + cw * i / (N - 1);
    const yEq = v => pad.top + eqH * (1 - (v - eqMin) / (eqMax - eqMin));
    const yDd = d => pad.top + eqH + 8 + ddH * d;

    // Grid
    drawGrid(ctx, w, h, { ...pad, bottom: pad.bottom }, eqMin, eqMax, N);

    // Equity fill
    ctx.beginPath();
    ctx.moveTo(xOf(0), yEq(equityCurve[0].equity));
    for (let i = 1; i < N; i++) ctx.lineTo(xOf(i), yEq(equityCurve[i].equity));
    ctx.lineTo(xOf(N-1), pad.top + eqH);
    ctx.lineTo(xOf(0),   pad.top + eqH);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + eqH);
    grad.addColorStop(0,   "rgba(0,200,180,0.22)");
    grad.addColorStop(1,   "rgba(0,200,180,0.01)");
    ctx.fillStyle = grad;
    ctx.fill();

    // Equity line
    ctx.beginPath();
    ctx.strokeStyle = C.teal;
    ctx.lineWidth   = 1.5;
    ctx.moveTo(xOf(0), yEq(equityCurve[0].equity));
    for (let i = 1; i < N; i++) ctx.lineTo(xOf(i), yEq(equityCurve[i].equity));
    ctx.stroke();

    // Drawdown fill
    ctx.beginPath();
    ctx.moveTo(xOf(0), yDd(0));
    for (let i = 1; i < N; i++) ctx.lineTo(xOf(i), yDd(ddSeries[i]));
    ctx.lineTo(xOf(N-1), yDd(0));
    ctx.lineTo(xOf(0),   yDd(0));
    ctx.closePath();
    const ddGrad = ctx.createLinearGradient(0, pad.top + eqH + 8, 0, pad.top + eqH + 8 + ddH);
    ddGrad.addColorStop(0, "rgba(220,40,60,0.45)");
    ddGrad.addColorStop(1, "rgba(220,40,60,0.05)");
    ctx.fillStyle = ddGrad;
    ctx.fill();

    // Drawdown line
    ctx.beginPath();
    ctx.strokeStyle = C.red;
    ctx.lineWidth   = 1;
    ctx.moveTo(xOf(0), yDd(0));
    for (let i = 1; i < N; i++) ctx.lineTo(xOf(i), yDd(ddSeries[i]));
    ctx.stroke();

    // Trade entry dots
    for (const t of trades) {
      const idx = equityCurve.findIndex(e => e.date >= t.exit_dt);
      if (idx < 0) continue;
      const x = xOf(idx);
      const y = yEq(equityCurve[idx].equity);
      ctx.beginPath();
      ctx.arc(x, y, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = t.realised_pnl >= 0 ? C.green : C.red;
      ctx.fill();
    }

    // Y-axis labels equity
    ctx.fillStyle  = C.muted;
    ctx.font       = `10px ${MONO}`;
    ctx.textAlign  = "right";
    for (let i = 0; i <= 4; i++) {
      const v = eqMin + (eqMax - eqMin) * i / 4;
      const y = yEq(v);
      ctx.fillText("$" + Math.round(v / 1000) + "k", pad.left - 6, y + 3);
    }

    // Y-axis labels drawdown
    ctx.fillStyle = "rgba(220,40,60,0.7)";
    const maxDd = Math.max(...ddSeries);
    if (maxDd > 0) {
      ctx.fillText("-" + (maxDd * 100).toFixed(1) + "%", pad.left - 6, yDd(maxDd) + 3);
    }

    // X-axis dates
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    const xStep = Math.max(1, Math.floor(N / 7));
    for (let i = 0; i < N; i += xStep) {
      ctx.fillText(equityCurve[i].date.slice(0, 7), xOf(i), h - pad.bottom + 14);
    }

    // Section labels
    ctx.fillStyle = C.teal;
    ctx.textAlign = "left";
    ctx.font      = `9px ${MONO}`;
    ctx.fillText("EQUITY", pad.left + 4, pad.top + 12);
    ctx.fillStyle = C.red;
    ctx.fillText("DRAWDOWN", pad.left + 4, pad.top + eqH + 20);

    // Hover crosshair
    if (hoverIdx !== null && hoverIdx < N) {
      const x = xOf(hoverIdx);
      ctx.strokeStyle = "rgba(184,200,208,0.25)";
      ctx.lineWidth   = 0.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, h - pad.bottom); ctx.stroke();
      ctx.setLineDash([]);
      // Dot on equity line
      const y = yEq(equityCurve[hoverIdx].equity);
      ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = C.teal2; ctx.fill();
    }
  }, [equityCurve, trades, eqMin, eqMax, ddSeries, hoverIdx, pad]);

  const canvasRef = useCanvas(draw, [draw]);

  const onMouseMove = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x    = e.clientX - rect.left;
    const cw   = rect.width - pad.left - pad.right;
    const idx  = Math.round((x - pad.left) / cw * (equityCurve.length - 1));
    setHoverIdx(Math.max(0, Math.min(equityCurve.length - 1, idx)));
  }, [equityCurve.length, pad.left, pad.right, setHoverIdx]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width:"100%", height:"100%", cursor:"crosshair", display:"block" }}
      onMouseMove={onMouseMove}
      onMouseLeave={() => setHoverIdx(null)}
    />
  );
}

/* ─── Rolling Sharpe chart ────────────────────────────────────────────────── */
function SharpeChart({ trades }) {
  const pad = { top:16, right:16, bottom:28, left:52 };

  const series = useMemo(() => {
    if (trades.length < 10) return [];
    const window = 20;
    const result = [];
    for (let i = window; i <= trades.length; i++) {
      const slice = trades.slice(i - window, i);
      const rs    = slice.map(t => t.realised_pnl);
      const mean  = rs.reduce((a,b)=>a+b,0) / rs.length;
      const std   = Math.sqrt(rs.reduce((a,b)=>a+(b-mean)**2,0) / (rs.length-1));
      result.push({ x: i, sharpe: std > 0 ? (mean / std) * Math.sqrt(252 / window) : 0, date: trades[i-1].exit_dt });
    }
    return result;
  }, [trades]);

  const draw = useCallback((ctx, w, h) => {
    if (!series.length) return;
    ctx.clearRect(0, 0, w, h);
    const cw = w - pad.left - pad.right;
    const ch = h - pad.top  - pad.bottom;
    const vals = series.map(s => s.sharpe);
    const yMin = Math.min(...vals, -0.5) * 1.1;
    const yMax = Math.max(...vals,  0.5) * 1.1;
    const N    = series.length;

    const xOf = i => pad.left + cw * i / (N - 1);
    const yOf = v => pad.top  + ch * (1 - (v - yMin) / (yMax - yMin));
    const y0  = yOf(0);

    drawGrid(ctx, w, h, pad, yMin, yMax, N);

    // Zero line
    ctx.strokeStyle = C.border2;
    ctx.lineWidth   = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, y0); ctx.lineTo(w - pad.right, y0); ctx.stroke();

    // Fill above / below zero
    for (let i = 1; i < N; i++) {
      const x0s = xOf(i-1), x1s = xOf(i);
      const y0s = yOf(series[i-1].sharpe), y1s = yOf(series[i].sharpe);
      ctx.beginPath();
      ctx.moveTo(x0s, y0); ctx.lineTo(x0s, y0s); ctx.lineTo(x1s, y1s); ctx.lineTo(x1s, y0);
      ctx.closePath();
      ctx.fillStyle = series[i].sharpe >= 0 ? "rgba(0,200,180,0.15)" : "rgba(220,40,60,0.15)";
      ctx.fill();
    }

    // Line
    ctx.beginPath();
    ctx.lineWidth = 1.5;
    ctx.moveTo(xOf(0), yOf(series[0].sharpe));
    for (let i = 1; i < N; i++) {
      ctx.strokeStyle = series[i].sharpe >= 0 ? C.teal : C.red;
      ctx.lineTo(xOf(i), yOf(series[i].sharpe));
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(xOf(i), yOf(series[i].sharpe));
    }

    // Y labels
    ctx.fillStyle = C.muted; ctx.font = `9px ${MONO}`; ctx.textAlign = "right";
    for (const v of [yMin, 0, yMax]) {
      ctx.fillText(v.toFixed(1), pad.left - 5, yOf(v) + 3);
    }
    ctx.fillStyle = C.muted; ctx.textAlign = "center";
    const step = Math.max(1, Math.floor(N / 5));
    for (let i = 0; i < N; i += step) {
      ctx.fillText(series[i].date.slice(0,7), xOf(i), h - 6);
    }

    ctx.fillStyle = C.amber; ctx.textAlign = "left"; ctx.font = `9px ${MONO}`;
    ctx.fillText("ROLLING SHARPE (20-trade)", pad.left + 4, pad.top + 11);
  }, [series, pad]);

  const ref = useCanvas(draw, [draw]);
  return <canvas ref={ref} style={{ width:"100%", height:"100%", display:"block" }} />;
}

/* ─── R-multiple scatter ──────────────────────────────────────────────────── */
function RScatter({ trades }) {
  const pad = { top:16, right:16, bottom:28, left:52 };

  const draw = useCallback((ctx, w, h) => {
    if (!trades.length) return;
    ctx.clearRect(0, 0, w, h);
    const cw = w - pad.left - pad.right;
    const ch = h - pad.top  - pad.bottom;
    const rs   = trades.map(t => t.r_multiple);
    const rMin = Math.min(...rs, -3) - 0.2;
    const rMax = Math.max(...rs,  3) + 0.2;
    const N    = trades.length;

    const xOf = i => pad.left + cw * i / (N - 1);
    const yOf = v => pad.top  + ch * (1 - (v - rMin) / (rMax - rMin));
    const y0  = yOf(0);

    drawGrid(ctx, w, h, pad, rMin, rMax, N);

    // Zero line
    ctx.strokeStyle = C.border2; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, y0); ctx.lineTo(w - pad.right, y0); ctx.stroke();

    // Expectancy band
    const mean = rs.reduce((a,b)=>a+b,0)/rs.length;
    const yMean = yOf(mean);
    ctx.strokeStyle = "rgba(232,160,48,0.5)"; ctx.lineWidth = 0.8; ctx.setLineDash([5,3]);
    ctx.beginPath(); ctx.moveTo(pad.left, yMean); ctx.lineTo(w - pad.right, yMean); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = C.amber; ctx.font = `8px ${MONO}`; ctx.textAlign = "left";
    ctx.fillText(`avg R=${mean.toFixed(2)}`, pad.left + 4, yMean - 3);

    // Scatter dots
    for (let i = 0; i < N; i++) {
      const t = trades[i];
      ctx.beginPath();
      ctx.arc(xOf(i), yOf(t.r_multiple), 3, 0, Math.PI * 2);
      ctx.fillStyle = C.sector[t.sector] || C.muted;
      ctx.globalAlpha = 0.75;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    // Y labels
    ctx.fillStyle = C.muted; ctx.font = `9px ${MONO}`; ctx.textAlign = "right";
    for (const v of [Math.ceil(rMin), 0, Math.floor(rMax)]) {
      ctx.fillText(v + "R", pad.left - 5, yOf(v) + 3);
    }

    ctx.fillStyle = C.bright; ctx.textAlign = "left"; ctx.font = `9px ${MONO}`;
    ctx.fillText("R-MULTIPLE PER TRADE", pad.left + 4, pad.top + 11);
  }, [trades, pad]);

  const ref = useCanvas(draw, [draw]);
  return <canvas ref={ref} style={{ width:"100%", height:"100%", display:"block" }} />;
}

/* ─── Sector breakdown bar chart ──────────────────────────────────────────── */
function SectorBars({ bySector }) {
  const entries = Object.entries(bySector || {}).filter(([,v]) => v.trades > 0);
  if (!entries.length) return null;
  const maxAbs = Math.max(...entries.map(([,v]) => Math.abs(v.net_pnl)));
  return (
    <div style={{ padding:"10px 14px" }}>
      <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.14em", textTransform:"uppercase", marginBottom:8, fontFamily:MONO }}>Sector P&amp;L</div>
      {entries.map(([sec, v]) => {
        const pct = maxAbs > 0 ? Math.abs(v.net_pnl) / maxAbs : 0;
        const col = C.sector[sec] || C.muted;
        return (
          <div key={sec} style={{ marginBottom:6 }}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:2 }}>
              <span style={{ fontSize:9, color:col, fontFamily:MONO, textTransform:"uppercase", letterSpacing:"0.08em" }}>{sec}</span>
              <span style={{ fontSize:9, color: v.net_pnl >= 0 ? C.green : C.red, fontFamily:MONO }}>
                {v.net_pnl >= 0 ? "+" : ""}${Math.round(v.net_pnl).toLocaleString()}
              </span>
            </div>
            <div style={{ height:3, background:C.border, borderRadius:1, overflow:"hidden" }}>
              <div style={{ height:"100%", width:`${pct*100}%`, background: v.net_pnl >= 0 ? col : C.red, borderRadius:1, transition:"width 0.6s ease" }} />
            </div>
            <div style={{ display:"flex", gap:12, marginTop:2 }}>
              <span style={{ fontSize:8, color:C.muted, fontFamily:MONO }}>{v.trades} trades</span>
              <span style={{ fontSize:8, color:C.muted, fontFamily:MONO }}>WR {(v.win_rate*100).toFixed(0)}%</span>
              <span style={{ fontSize:8, color:C.amber, fontFamily:MONO }}>avgR {v.avg_r >= 0 ? "+" : ""}{v.avg_r}R</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Main component ──────────────────────────────────────────────────────── */
export default function BacktestVisualiser() {
  const [data,     setData]     = useState(null);
  const [hoverIdx, setHoverIdx] = useState(null);
  const [tab,      setTab]      = useState("equity"); // equity | sharpe | scatter
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => { setData(genDemo()); }, []);

  const onFile = useCallback((file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      try { setData(JSON.parse(e.target.result)); } catch { alert("Invalid JSON file."); }
    };
    reader.readAsText(file);
  }, []);

  const onDrop = useCallback(e => {
    e.preventDefault(); setDragging(false);
    onFile(e.dataTransfer.files[0]);
  }, [onFile]);

  const hovered = hoverIdx !== null && data?.equity_curve?.[hoverIdx];

  const tabStyle = (t) => ({
    fontFamily: MONO, fontSize:9, letterSpacing:"0.14em", textTransform:"uppercase",
    padding:"5px 12px", cursor:"pointer", border:"none", background:"transparent",
    color: tab === t ? C.teal : C.muted, borderBottom: `1px solid ${tab === t ? C.teal : "transparent"}`,
    transition:"color 0.15s",
  });

  if (!data) return <div style={{ background:C.bg, color:C.muted, padding:20, fontFamily:MONO, fontSize:11 }}>Loading…</div>;

  const { equity_curve: eq, trades } = data;

  return (
    <div
      style={{ background:C.bg, color:C.text, fontFamily:SANS, minHeight:"100vh", display:"flex", flexDirection:"column" }}
      onDragOver={e=>{e.preventDefault();setDragging(true);}}
      onDragLeave={()=>setDragging(false)}
      onDrop={onDrop}
    >
      {dragging && (
        <div style={{ position:"fixed", inset:0, background:"rgba(0,200,180,0.08)", border:`2px solid ${C.teal}`, zIndex:99, display:"flex", alignItems:"center", justifyContent:"center", pointerEvents:"none" }}>
          <span style={{ fontFamily:MONO, fontSize:13, color:C.teal }}>DROP JSON TO LOAD</span>
        </div>
      )}

      {/* Header */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"0 18px", height:42, borderBottom:`1px solid ${C.border}`, background:C.surface, flexShrink:0 }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <span style={{ fontFamily:MONO, fontSize:12, fontWeight:600, color:C.amber, letterSpacing:"0.1em" }}>CHIMERA BACKTEST</span>
          <span style={{ fontFamily:MONO, fontSize:9, color:C.muted }}>{eq[0]?.date} → {eq[eq.length-1]?.date}</span>
          <span style={{ fontFamily:MONO, fontSize:9, color:C.dim, background:C.panel, padding:"2px 7px", borderRadius:2, border:`1px solid ${C.border}` }}>{data.backtest_days}D</span>
        </div>
        <button
          onClick={() => fileRef.current?.click()}
          style={{ fontFamily:MONO, fontSize:9, letterSpacing:"0.12em", textTransform:"uppercase", padding:"4px 10px", background:C.panel, color:C.muted, border:`1px solid ${C.border}`, borderRadius:2, cursor:"pointer" }}
        >Load JSON</button>
        <input ref={fileRef} type="file" accept=".json" style={{ display:"none" }} onChange={e=>onFile(e.target.files[0])} />
      </div>

      {/* Stat strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(9, 1fr)", borderBottom:`1px solid ${C.border}`, background:C.surface, flexShrink:0 }}>
        <Stat label="Return" value={`${data.total_return_pct >= 0 ? "+" : ""}${data.total_return_pct}%`} color={data.total_return_pct >= 0 ? C.green : C.red} />
        <Stat label="CAGR"   value={`${data.cagr_pct >= 0 ? "+" : ""}${data.cagr_pct}%`}   color={data.cagr_pct >= 0 ? C.teal : C.red} />
        <Stat label="Max DD" value={`-${data.max_drawdown_pct}%`} color={C.red} />
        <Stat label="Sharpe" value={data.sharpe_ratio}  color={data.sharpe_ratio > 1 ? C.green : C.amber} />
        <Stat label="Sortino" value={data.sortino_ratio} color={data.sortino_ratio > 1 ? C.green : C.amber} />
        <Stat label="Calmar" value={data.calmar_ratio}  color={data.calmar_ratio > 0.5 ? C.teal : C.muted} />
        <Stat label="Win rate" value={`${(data.win_rate*100).toFixed(1)}%`} sub={`${data.total_trades} trades`} color={data.win_rate > 0.55 ? C.green : C.muted} />
        <Stat label="Pf" value={data.profit_factor}  color={data.profit_factor > 1.5 ? C.green : C.amber} sub="profit factor" />
        <Stat label="Expectancy" value={`${data.expectancy_r >= 0 ? "+" : ""}${data.expectancy_r}R`} color={data.expectancy_r > 0 ? C.teal : C.red} />
      </div>

      {/* Body */}
      <div style={{ display:"flex", flex:1, overflow:"hidden", minHeight:0 }}>

        {/* Main charts */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", minWidth:0 }}>

          {/* Tab bar */}
          <div style={{ display:"flex", borderBottom:`1px solid ${C.border}`, background:C.surface, paddingLeft:4, flexShrink:0 }}>
            {[["equity","Equity + Drawdown"],["sharpe","Rolling Sharpe"],["scatter","R-Multiple Scatter"]].map(([id,label])=>(
              <button key={id} style={tabStyle(id)} onClick={()=>setTab(id)}>{label}</button>
            ))}
            {hovered && (
              <div style={{ marginLeft:"auto", display:"flex", gap:16, alignItems:"center", paddingRight:16 }}>
                <span style={{ fontFamily:MONO, fontSize:9, color:C.dim }}>{hovered.date}</span>
                <span style={{ fontFamily:MONO, fontSize:11, color:C.teal2 }}>${hovered.equity.toLocaleString("en-US",{maximumFractionDigits:0})}</span>
                <span style={{ fontFamily:MONO, fontSize:9, color:C.muted }}>
                  {hovered.equity >= data.initial_equity ? "+" : ""}{((hovered.equity/data.initial_equity-1)*100).toFixed(2)}%
                </span>
              </div>
            )}
          </div>

          {/* Chart area */}
          <div style={{ flex:1, position:"relative", minHeight:0 }}>
            <div style={{ position:"absolute", inset:0, display: tab==="equity"  ? "block" : "none" }}>
              <EquityChart equityCurve={eq} trades={trades} hoverIdx={hoverIdx} setHoverIdx={setHoverIdx} />
            </div>
            <div style={{ position:"absolute", inset:0, display: tab==="sharpe"  ? "block" : "none" }}>
              <SharpeChart trades={trades} />
            </div>
            <div style={{ position:"absolute", inset:0, display: tab==="scatter" ? "block" : "none" }}>
              <RScatter trades={trades} />
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div style={{ width:220, borderLeft:`1px solid ${C.border}`, background:C.surface, display:"flex", flexDirection:"column", overflow:"auto", flexShrink:0 }}>

          <SectorBars bySector={data.by_sector} />

          {/* Exit reasons */}
          <div style={{ padding:"10px 14px", borderTop:`1px solid ${C.border}` }}>
            <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.14em", textTransform:"uppercase", marginBottom:8, fontFamily:MONO }}>Exit reasons</div>
            {Object.entries(data.close_reasons || {}).map(([r, n]) => (
              <div key={r} style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
                <span style={{ fontSize:9, color:C.reason[r] || C.muted, fontFamily:MONO }}>{r.replace("_"," ")}</span>
                <span style={{ fontSize:9, color:C.bright, fontFamily:MONO }}>{n}</span>
              </div>
            ))}
          </div>

          {/* Sector legend */}
          <div style={{ padding:"10px 14px", borderTop:`1px solid ${C.border}` }}>
            <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.14em", textTransform:"uppercase", marginBottom:8, fontFamily:MONO }}>Sector colour</div>
            {Object.entries(C.sector).map(([s, c]) => (
              <div key={s} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:4 }}>
                <div style={{ width:8, height:8, borderRadius:"50%", background:c, flexShrink:0 }} />
                <span style={{ fontSize:9, color:C.muted, fontFamily:MONO, textTransform:"uppercase" }}>{s}</span>
              </div>
            ))}
          </div>

          {/* Last 8 trades */}
          <div style={{ padding:"10px 14px", borderTop:`1px solid ${C.border}`, flex:1 }}>
            <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.14em", textTransform:"uppercase", marginBottom:8, fontFamily:MONO }}>Recent trades</div>
            {[...trades].slice(-8).reverse().map((t, i) => (
              <div key={i} style={{ marginBottom:6, paddingBottom:6, borderBottom:`1px solid ${C.border}` }}>
                <div style={{ display:"flex", justifyContent:"space-between" }}>
                  <span style={{ fontSize:10, color:C.sector[t.sector]||C.muted, fontFamily:MONO, fontWeight:500 }}>{t.symbol}</span>
                  <span style={{ fontSize:10, color:t.realised_pnl>=0?C.green:C.red, fontFamily:MONO }}>{t.realised_pnl>=0?"+":""}${Math.round(t.realised_pnl).toLocaleString()}</span>
                </div>
                <div style={{ display:"flex", justifyContent:"space-between", marginTop:1 }}>
                  <span style={{ fontSize:8, color:C.muted, fontFamily:MONO }}>{t.exit_dt}</span>
                  <span style={{ fontSize:8, color:t.r_multiple>=0?C.teal:C.red, fontFamily:MONO }}>{t.r_multiple>=0?"+":""}{t.r_multiple}R</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
