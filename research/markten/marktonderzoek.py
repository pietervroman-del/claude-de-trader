"""Marktonderzoek: de 50-dagenregel van Claude de Trader op 18 markten.

Regel: alles in de markt als de gesloten dag boven het N-dagengemiddelde sloot, anders alles in cash (geen short).
Fee per transactie (standaard 0,4%). Uitvoering aan het dagslot. Twee periodes:
  recent  15 nov 2023 - nu      (de periode waarop de regel voor ETH gekozen werd)
  ervoor  15 nov 2020 - 15 nov 2023 (controle in een andere marktfase)
Data: markten.json (Binance voor crypto, Yahoo Finance voor de rest).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA = json.loads(Path(__file__).with_name("markten.json").read_text())
PERIODES = {"recent": (datetime(2023, 11, 15), None), "ervoor": (datetime(2020, 11, 15), datetime(2023, 11, 15))}
GROEP = {"BTC": "crypto", "ETH": "crypto", "SOL": "crypto", "XRP": "crypto", "BNB": "crypto", "ADA": "crypto",
         "DOGE": "crypto", "LINK": "crypto", "Goud": "grondstof", "Zilver": "grondstof", "Olie (WTI)": "grondstof",
         "S&P 500": "aandelen", "Nasdaq 100": "aandelen", "Euro Stoxx 50": "aandelen", "Bel 20": "aandelen",
         "EUR/USD": "forex", "GBP/USD": "forex", "USD/JPY": "forex"}


def run(rows, start, end, n=50, fee=0.004):
    ts = [r[0] for r in rows]; cl = [r[1] for r in rows]
    s = start.replace(tzinfo=timezone.utc).timestamp()
    e = end.replace(tzinfo=timezone.utc).timestamp() if end else 1e12
    i0 = next(i for i, t in enumerate(ts) if t >= s and i >= n)
    i1 = max(i for i, t in enumerate(ts) if t < e) + 1
    cash, units, inpos, trades = 1.0, 0.0, False, 0
    peak = mdd = hpeak = hmdd = 0
    for i in range(i0, i1):
        px = cl[i]; m = sum(cl[i - n + 1:i + 1]) / n
        if px > m and not inpos:
            units = cash * (1 - fee) / px; cash = 0; inpos = True; trades += 1
        elif px < m and inpos:
            cash = units * px * (1 - fee); units = 0; inpos = False; trades += 1
        v = cash + units * px
        peak = max(peak, v); mdd = max(mdd, 1 - v / peak)
        h = px / cl[i0]; hpeak = max(hpeak, h); hmdd = max(hmdd, 1 - h / hpeak)
    strat = cash + units * cl[i1 - 1]
    hold = cl[i1 - 1] / cl[i0]
    return {"strat": strat, "hold": hold, "ratio": strat / hold, "trades": trades, "mdd": mdd, "hmdd": hmdd}


def pct(x):
    return f"{(x - 1) * 100:+.0f}%"


if __name__ == "__main__":
    print(f"{'markt':<14} {'groep':<9} | RECENT (nov 23-nu): regel / houden / verhouding / trades / daling regel-houden"
          f" | ERVOOR (nov 20-nov 23): verhouding | 40d / 60d (recent) | fee 0,1% (recent)")
    for name, rows in DATA.items():
        r = run(rows, *PERIODES["recent"]); o = run(rows, *PERIODES["ervoor"])
        r40 = run(rows, *PERIODES["recent"], n=40)["ratio"]; r60 = run(rows, *PERIODES["recent"], n=60)["ratio"]
        rf = run(rows, *PERIODES["recent"], fee=0.001)["ratio"]
        print(f"{name:<14} {GROEP[name]:<9} | {pct(r['strat']):>6} / {pct(r['hold']):>6} / {r['ratio']:5.2f} / {r['trades']:>3} / "
              f"{r['mdd']:4.0%}-{r['hmdd']:4.0%} | {o['ratio']:5.2f} | {r40:5.2f} / {r60:5.2f} | {rf:5.2f}")
