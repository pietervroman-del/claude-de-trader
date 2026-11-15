"""Schrijft docs/backtest.json: de huidige botregel nagespeeld op ETH/EUR vanaf 15 nov 2023 met EUR 1.000.

Regel: 100% ETH als de gesloten dag boven het 50-dagengemiddelde sloot, anders 100% euro. Fee 0,4%.
Gebruikt research/eth_eur_daily_binance.json (Binance ETH/EUR dagcandles).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

FEE, N, START = 0.004, 50, datetime(2023, 11, 15, tzinfo=timezone.utc)
here = Path(__file__).resolve().parent
rows = json.loads((here / "eth_eur_daily_binance.json").read_text())[:-1]   # lopende dag weg
t = [r[0] for r in rows]
cl = [r[4] for r in rows]
i0 = next(i for i, x in enumerate(t) if x >= START.timestamp())

cash, eth, inpos = 1000.0, 0.0, False
candles, sma, equity, hold, trades = [], [], [], [], []
start_px = cl[i0]
for i in range(i0, len(rows)):
    m = sum(cl[i - N + 1:i + 1]) / N
    px = cl[i]
    if px > m and not inpos:
        eth = cash * (1 - FEE) / px; cash = 0; inpos = True
        trades.append({"t": t[i], "side": "buy", "px": round(px, 2), "waarde": round(eth * px, 2)})
    elif px < m and inpos:
        cash = eth * px * (1 - FEE); eth = 0; inpos = False
        buy = trades[-1]["px"]
        trades.append({"t": t[i], "side": "sell", "px": round(px, 2), "waarde": round(cash, 2),
                       "rend": round((px * (1 - FEE) ** 2 / buy - 1) * 100, 1)})
    candles.append([t[i], rows[i][1], rows[i][2], rows[i][3], px])
    sma.append([t[i], round(m, 2)])
    equity.append([t[i], round(cash + eth * px, 2)])
    hold.append([t[i], round(1000 / start_px * px, 2)])

out = {"gemaakt": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "start": t[i0], "sma_dagen": N, "fee": FEE,
       "candles": candles, "sma": sma, "equity": equity, "hold": hold, "trades": trades,
       "eind": equity[-1][1], "eind_houden": hold[-1][1]}
(here.parent / "docs" / "backtest.json").write_text(json.dumps(out), encoding="utf-8")
sells = [x for x in trades if x["side"] == "sell"]
print(f"{len(candles)} dagen, {len(trades)} transacties, {sum(x['rend'] > 0 for x in sells)}/{len(sells)} winst, "
      f"eind EUR {out['eind']:,.0f} vs houden EUR {out['eind_houden']:,.0f}")
