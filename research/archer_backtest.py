"""Backtest van de "Archer"-methode (Mind to Invest) op ETH-weekcandles, tegenover gewoon ETH houden.

Hun regels, zoals in 12 afleveringen uitgelegd, vertaald naar vaste code. Waar zij iets alleen op het scherm
toonden, staat de gekozen invulling met (KEUZE) gemarkeerd.

1. Tijdframe: weekcandles; een candle telt pas na de sluiting.
2. Structuur: swing highs/lows via zigzag (KEUZE: een top/bodem telt na P% terugkeer, bv. 25%).
   Bullish = laatste high > vorige high én laatste low > vorige low. Bearish = omgekeerd.
3. Instap A (pullback): bullish structuur; de week raakt de Fibonacci-retracementzone 61,8%-78,6% (KEUZE: 78,6
   als ondergrens) van de laatste impuls (low -> high) en sluit als bullish candle binnen of boven de zone.
   Instap B (momentum-switch): bearish structuur en een bullish weekslot boven de laatste lower high.
4. Stop: A net onder de zone (0,886-retracement), B onder de low van de doorbraakweken; max 20% risico (KEUZE).
5. Doel 1: de -0,27-extensie van de impuls (A) of 3x het risico (B). Alleen instappen bij winst >= 3x risico.
   Op doel 1: helft verkopen, stop naar instap (breakeven).
6. Rest: verkopen bij een weekslot onder de laatste higher low, of op de -0,618-extensie (doel 2).
7. Fee 0,4% per transactie. Spot, geen hefboom, volledige positie (KEUZE: geen inschalen).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FEE = 0.004


def load(path):
    r = json.loads(Path(path).read_text())["result"]
    rows = r[next(k for k in r if k != "last")]
    return [{"t": datetime.fromtimestamp(x[0], timezone.utc), "o": float(x[1]), "h": float(x[2]),
             "l": float(x[3]), "c": float(x[4])} for x in rows]


def pivots(w, P):
    """Zigzag: een top/bodem is bevestigd zodra de prijs er P (bv. 0.25 = 25%) van terugkeert.
    Lijst (bekend_op_index, index, 'H'/'L', prijs); geen kijken in de toekomst."""
    out, mode = [], None
    ext_i = 0
    for i in range(1, len(w)):
        if mode in (None, "up"):
            if w[i]["h"] >= w[ext_i]["h"] or mode is None and w[i]["h"] > w[ext_i]["h"]:
                ext_i = i if mode == "up" or w[i]["h"] > w[ext_i]["h"] else ext_i
            if mode == "up" and w[i]["l"] <= w[ext_i]["h"] * (1 - P):
                out.append((i, ext_i, "H", w[ext_i]["h"])); mode, ext_i = "down", i
                continue
        if mode in (None, "down"):
            if mode == "down" and w[i]["l"] <= w[ext_i]["l"]:
                ext_i = i
            if mode == "down" and w[i]["h"] >= w[ext_i]["l"] * (1 + P):
                out.append((i, ext_i, "L", w[ext_i]["l"])); mode, ext_i = "up", i
                continue
        if mode is None:
            lo = min(range(i + 1), key=lambda j: w[j]["l"]); hi = max(range(i + 1), key=lambda j: w[j]["h"])
            if w[i]["h"] >= w[lo]["l"] * (1 + P):
                out.append((i, lo, "L", w[lo]["l"])); mode, ext_i = "up", i
            elif w[i]["l"] <= w[hi]["h"] * (1 - P):
                out.append((i, hi, "H", w[hi]["h"])); mode, ext_i = "down", i
    return out


def run(w, K=0.25, start=0, rr_min=3.0, max_risk=0.20):
    piv = pivots(w, K)
    cash, eth = 1.0, 0.0           # start met 1 eenheid geld, in cash
    pos = None                      # dict met entry, stop, t1, t2, half_done
    trades, equity = [], []
    for i in range(start, len(w)):
        c = w[i]
        known = [p for p in piv if p[0] <= i]
        highs = [p for p in known if p[2] == "H"]
        lows = [p for p in known if p[2] == "L"]

        # 1) lopende positie beheren (intrabar: stop eerst, conservatief)
        if pos:
            if c["l"] <= pos["stop"]:
                px = min(c["o"], pos["stop"])
                cash += eth * px * (1 - FEE); trades[-1]["exit"].append((c["t"], px, "stop")); eth = 0; pos = None
            else:
                if not pos["half"] and c["h"] >= pos["t1"]:
                    sell = eth / 2
                    cash += sell * pos["t1"] * (1 - FEE); eth -= sell
                    pos["half"] = True; pos["stop"] = max(pos["stop"], pos["entry"])
                    trades[-1]["exit"].append((c["t"], pos["t1"], "doel1"))
                if pos and pos["half"] and c["h"] >= pos["t2"]:
                    cash += eth * pos["t2"] * (1 - FEE); trades[-1]["exit"].append((c["t"], pos["t2"], "doel2")); eth = 0; pos = None
                elif pos and pos["half"] and lows and c["c"] < lows[-1][3]:
                    cash += eth * c["c"] * (1 - FEE); trades[-1]["exit"].append((c["t"], c["c"], "structuur")); eth = 0; pos = None

        # 2) instap zoeken (alleen als vlak)
        elif len(highs) >= 2 and len(lows) >= 2:
            H1, H2, L1, L2 = highs[-2][3], highs[-1][3], lows[-2][3], lows[-1][3]
            bull, bear = H2 > H1 and L2 > L1, H2 < H1 and L2 < L1
            green = c["c"] > c["o"]
            signal = None
            if bull and highs[-1][1] > lows[-1][1]:          # impuls van L2 naar H2 is de laatste beweging
                R = H2 - L2
                top, bot = H2 - 0.618 * R, H2 - 0.786 * R
                if c["l"] <= top and green and c["c"] >= bot:
                    stop = (H2 - 0.886 * R) * 0.99          # KEUZE: stop net onder de zone (0,886)
                    signal = ("A", stop, H2 + 0.27 * R, H2 + 0.618 * R)
            elif bear and green and c["c"] > H2:
                stop = min(c["l"], w[i - 1]["l"]) * 0.99      # KEUZE: onder de low van de doorbraakweken
                risk = c["c"] - stop
                signal = ("B", stop, c["c"] + 3 * risk, c["c"] + 6 * risk)
            if signal:
                kind, stop, t1, t2 = signal
                entry = c["c"]
                if entry > stop and (entry - stop) / entry <= max_risk and (t1 - entry) >= rr_min * (entry - stop):
                    eth = cash * (1 - FEE) / entry; cash = 0
                    pos = {"entry": entry, "stop": stop, "t1": t1, "t2": t2, "half": False}
                    trades.append({"kind": kind, "t": c["t"], "entry": entry, "stop": stop, "t1": t1, "exit": []})
        equity.append((c["t"], cash + eth * c["c"]))
    return trades, equity


def stats(equity, w, start):
    v0, v1 = equity[0][1], equity[-1][1]
    hold = w[-1]["c"] / w[start]["o"]
    years = (equity[-1][0] - equity[0][0]).days / 365.25
    peak, mdd = 0, 0
    for _, v in equity:
        peak = max(peak, v); mdd = max(mdd, 1 - v / peak)
    hpeak, hmdd = 0, 0
    for x in w[start:]:
        hpeak = max(hpeak, x["c"]); hmdd = max(hmdd, 1 - x["c"] / hpeak)
    return {"jaren": round(years, 1), "strategie_x": round(v1 / v0, 2), "houden_x": round(hold, 2),
            "strategie_in_eth": round((v1 / v0) / hold, 3), "max_daling_strat": f"{mdd:.0%}", "max_daling_houden": f"{hmdd:.0%}"}


if __name__ == "__main__":
    w = load(Path(__file__).with_name("eth_weekly.json"))
    K = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
    for label, start_date in [("volledig (2016-)", "2016-01-01"), ("sinds 2020", "2020-01-01"),
                              ("sinds 2022", "2022-01-01"), ("sinds 2024", "2024-01-01")]:
        sd = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        start = next(i for i, x in enumerate(w) if x["t"] >= sd)
        trades, eq = run(w, K, start)
        wins = sum(1 for t in trades if t["exit"] and t["exit"][-1][1] > t["entry"])
        print(label, stats(eq, w, start), f"trades={len(trades)} winst={wins}")
    if "-v" in sys.argv:
        trades, _ = run(w, K, 0)
        for t in trades:
            ex = " ; ".join(f"{e[0]:%Y-%m-%d} {e[1]:,.0f} {e[2]}" for e in t["exit"])
            print(f"{t['kind']} {t['t']:%Y-%m-%d} in {t['entry']:,.0f} stop {t['stop']:,.0f} doel1 {t['t1']:,.0f} -> {ex}")
