"""Speelt de huidige botregel na vanaf 15 nov 2023 met EUR 1.000 (ETH/EUR, cash in euro).

Regel: doel 100% ETH als de laatste gesloten dag boven het 50-dagengemiddelde sloot, anders 0% (kern 0%).
Bijsturen bij > 5 procentpunt afwijking, 0,4% fee per transactie, uitvoering aan het dagslot.
Vergelijkt met: EUR 1.000 in ETH op dag één en laten staan, en met kern 50% (zelfde regel).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FEE, N, DREMPEL = 0.004, 50, 0.05


def load(fn):
    rows = json.loads(Path(__file__).with_name(fn).read_text())[:-1]
    return [(datetime.fromtimestamp(r[0], timezone.utc), r[4]) for r in rows]


def replay(d, start, kern, verbose=False):
    cl = [c for _, c in d]
    i0 = next(i for i, (t, _) in enumerate(d) if t >= start)
    cash, eth, trades, log = 1000.0, 0.0, 0, []
    worst = (0, None)
    peak = 0
    mdd = 0
    for i in range(i0, len(d)):
        t, px = d[i]
        sma = sum(cl[i - N + 1:i + 1]) / N
        doel = 1.0 if px > sma else kern
        v = cash + eth * px
        nu = eth * px / v
        if abs(doel - nu) > DREMPEL or (i == i0 and doel > 0):
            diff = doel * v - eth * px
            if diff > 0:
                cash -= diff; eth += diff * (1 - FEE) / px; side = "koop"
            else:
                q = -diff / px; eth -= q; cash += q * px * (1 - FEE); side = "verkoop"
            trades += 1
            log.append((t, side, px, cash + eth * px))
        v = cash + eth * px
        hold = 1000.0 / d[i0][1] * px
        if 1 - v / hold > worst[0]:
            worst = (1 - v / hold, t, v, hold)
        peak = max(peak, v); mdd = max(mdd, 1 - v / peak)
    end = cash + eth * d[-1][1]
    return {"eind": end, "houden": 1000.0 / d[i0][1] * d[-1][1], "trades": trades, "worst": worst, "mdd": mdd,
            "log": log, "start_px": d[i0][1], "eind_px": d[-1][1], "eth": eth, "cash": cash}


if __name__ == "__main__":
    start = datetime(2023, 11, 15, tzinfo=timezone.utc)
    for fn, cur in (("eth_eur_daily_binance.json", "EUR"), ("eth_daily_binance.json", "USD")):
        d = load(fn)
        for kern in (0.0, 0.5):
            r = replay(d, start, kern)
            w = r["worst"]
            print(f"[{cur}] kern {kern:.0%}: 1.000 -> {r['eind']:,.0f}  | houden: {r['houden']:,.0f} | "
                  f"{r['trades']} transacties | grootste daling eigen waarde {r['mdd']:.0%} | "
                  f"slechtste achterstand op houden {w[0]:.0%} op {w[1]:%d %b %Y} ({w[2]:,.0f} vs {w[3]:,.0f})")
        print(f"   ETH {r['start_px']:,.0f} -> {r['eind_px']:,.0f} {cur}")
    if "-v" in sys.argv:
        r = replay(load("eth_eur_daily_binance.json"), start, 0.0)
        wins = 0
        for (t, side, px, v) in r["log"]:
            print(f"  {t:%d-%m-%Y} {side:<8} ETH {px:>7,.0f} EUR  waarde na trade {v:>7,.0f}")
        sells = [(i, x) for i, x in enumerate(r["log"]) if x[1] == "verkoop"]
        for i, s in sells:
            buy = r["log"][i - 1] if i > 0 and r["log"][i - 1][1] == "koop" else None
            if buy and s[2] > buy[2] * (1 + 2 * FEE):
                wins += 1
        print(f"  verkopen boven de vorige aankoopprijs (+fees): {wins} van {len(sells)}")
