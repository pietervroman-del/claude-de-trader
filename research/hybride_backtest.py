"""Vergelijkt strategieën op ETH-weekcandles (Kraken), standaard 2021 – nu, gemeten tegenover gewoon ETH houden.

Varianten:
  houden       100% ETH, nooit handelen
  archer       Archer puur: 0% of 100% ETH op hun signalen (zie archer_backtest.py)
  trend        100% ETH boven het 30-wekengemiddelde (SMA30w), anders 100% cash
  kern+trend   50% kern altijd ETH; de andere 50% in ETH boven SMA30w, anders cash
  kern+archer  50% kern (25% in een bearmarkt: onder SMA30w én dalende structuur);
               tactische 50% op Archer-signalen met risico 2% van de portefeuille per trade,
               stop = ruimste van 88,6%-retracement en 2x ATR, inschalen in 2 stukken.

Instellingen zijn vooraf gekozen en niet op de resultaten afgesteld; `robuust` test buren ervan.
Alle transacties betalen 0,4% fee. Signalen gebruiken enkel gesloten weekcandles (geen blik in de toekomst).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FEE = 0.004


def load():
    r = json.loads(Path(__file__).with_name("eth_weekly.json").read_text())["result"]
    rows = r[next(k for k in r if k != "last")][:-1]   # lopende week weg
    return [{"t": datetime.fromtimestamp(x[0], timezone.utc), "o": float(x[1]), "h": float(x[2]),
             "l": float(x[3]), "c": float(x[4])} for x in rows]


def zigzag_known(w, p):
    """Per week: lijst bevestigde pivots (index, 'H'/'L', prijs) die op dat moment bekend zijn."""
    known, out, mode, ext = [], [], None, 0
    for i in range(len(w)):
        if i > 0:
            if mode is None:
                lo = min(range(i + 1), key=lambda j: w[j]["l"]); hi = max(range(i + 1), key=lambda j: w[j]["h"])
                if w[i]["h"] >= w[lo]["l"] * (1 + p):
                    out.append((lo, "L", w[lo]["l"])); mode, ext = "up", i
                elif w[i]["l"] <= w[hi]["h"] * (1 - p):
                    out.append((hi, "H", w[hi]["h"])); mode, ext = "down", i
            elif mode == "up":
                if w[i]["h"] >= w[ext]["h"]:
                    ext = i
                elif w[i]["l"] <= w[ext]["h"] * (1 - p):
                    out.append((ext, "H", w[ext]["h"])); mode, ext = "down", i
            else:
                if w[i]["l"] <= w[ext]["l"]:
                    ext = i
                elif w[i]["h"] >= w[ext]["l"] * (1 + p):
                    out.append((ext, "L", w[ext]["l"])); mode, ext = "up", i
        known.append(list(out))
    return known


def indicators(w, sma_n):
    sma, atr = [], []
    for i in range(len(w)):
        cs = [x["c"] for x in w[max(0, i - sma_n + 1):i + 1]]
        sma.append(sum(cs) / len(cs) if len(cs) == sma_n else None)
        trs = [max(w[j]["h"], w[j - 1]["c"]) - min(w[j]["l"], w[j - 1]["c"]) for j in range(max(1, i - 13), i + 1)]
        atr.append(sum(trs) / len(trs) if trs else None)
    return sma, atr


def structure(piv):
    highs = [x for x in piv if x[1] == "H"]; lows = [x for x in piv if x[1] == "L"]
    if len(highs) < 2 or len(lows) < 2:
        return None
    return {"H1": highs[-2][2], "H2": highs[-1][2], "L1": lows[-2][2], "L2": lows[-1][2],
            "lo_imp": next((x[2] for x in reversed(lows) if x[0] < highs[-1][0]), None)}


class Book:
    def __init__(self, price):
        self.cash, self.eth, self.trades = 1.0, 0.0, 0

    def to_eth_frac(self, frac, px):
        """Herbalanceer naar `frac` van de portefeuille in ETH."""
        eq = self.cash + self.eth * px
        diff = frac * eq - self.eth * px
        if abs(diff) < 0.01 * eq:
            return
        self.trades += 1
        if diff > 0:
            self.cash -= diff; self.eth += diff * (1 - FEE) / px
        else:
            q = -diff / px; self.eth -= q; self.cash += q * px * (1 - FEE)

    def value(self, px):
        return self.cash + self.eth * px


def simulate(w, variant, start, zz=0.25, sma_n=30, risk=0.02):
    known = zigzag_known(w, zz)
    sma, atr = indicators(w, sma_n)
    b = Book(w[start]["o"])
    core = 0.5
    tac = None          # tactische positie: dict met eth, entry, stop, t1, t2, half, tranche2
    eq = []
    if variant == "houden":
        b.to_eth_frac(1.0, w[start]["o"])
    for i in range(start, len(w)):
        c, px = w[i], w[i]["c"]
        st = structure(known[i])
        above = sma[i] is not None and px > sma[i]

        if variant == "trend":
            b.to_eth_frac(1.0 if above else 0.0, px)
        elif variant == "kern+trend":
            b.to_eth_frac(1.0 if above else 0.5, px)
        elif variant in ("archer", "kern+archer"):
            bear = st and st["H2"] < st["H1"] and st["L2"] < st["L1"] and not above
            core_target = (0.25 if bear else 0.5) if variant == "kern+archer" else 0.0
            # 1) tactische positie beheren (intrabar, stop eerst)
            if tac:
                if c["l"] <= tac["stop"]:
                    out = min(c["o"], tac["stop"]); b.eth -= tac["eth"]; b.cash += tac["eth"] * out * (1 - FEE); b.trades += 1; tac = None
                else:
                    if not tac["half"] and c["h"] >= tac["t1"]:
                        q = tac["eth"] / 2; b.eth -= q; b.cash += q * tac["t1"] * (1 - FEE); b.trades += 1
                        tac["eth"] -= q; tac["half"] = True; tac["stop"] = max(tac["stop"], tac["entry"])
                    if tac and tac["half"] and c["h"] >= tac["t2"]:
                        b.eth -= tac["eth"]; b.cash += tac["eth"] * tac["t2"] * (1 - FEE); b.trades += 1; tac = None
                    elif tac and tac["half"] and st and px < st["L2"]:
                        b.eth -= tac["eth"]; b.cash += tac["eth"] * px * (1 - FEE); b.trades += 1; tac = None
                    elif tac and not tac["half"] and not tac["tranche2"] and px > c["o"] and px > tac["entry"]:
                        add = min(tac["size2"], b.cash)       # tweede stuk na bevestiging (groene week erboven)
                        if add > 0:
                            b.cash -= add; q = add * (1 - FEE) / px; b.eth += q; tac["eth"] += q; b.trades += 1
                        tac["tranche2"] = True
            # 2) nieuw signaal
            elif st and st["lo_imp"]:
                green = px > c["o"]
                R = st["H2"] - st["lo_imp"]
                sig = None
                if st["H2"] > st["H1"] and green and c["l"] <= st["H2"] - 0.618 * R and px >= st["H2"] - 0.786 * R:
                    stop = st["H2"] - 0.886 * R
                    sig = (stop, st["H2"] + 0.27 * R, st["H2"] + 0.618 * R)
                elif st["H2"] < st["H1"] and green and px > st["H2"]:
                    stop = min(c["l"], w[i - 1]["l"])
                    sig = (stop, px + 3 * (px - stop), px + 6 * (px - stop))
                if sig:
                    stop, t1, t2 = sig
                    if variant == "kern+archer" and atr[i]:
                        stop = min(stop, px - 2 * atr[i])
                    stop *= 0.99
                    if px > stop and (t1 - px) >= 3 * (px - stop):
                        equity = b.value(px)
                        if variant == "archer":
                            budget = b.cash
                            size1, size2 = budget, 0.0
                        else:
                            budget = min(b.cash, equity * 0.5)
                            full = min(budget, equity * risk / ((px - stop) / px))
                            size1, size2 = full / 2, full / 2
                        if size1 > 0:
                            b.cash -= size1; q = size1 * (1 - FEE) / px; b.eth += q; b.trades += 1
                            tac = {"eth": q, "entry": px, "stop": stop, "t1": t1, "t2": t2, "half": False,
                                   "tranche2": size2 == 0, "size2": size2}
            # 3) kern bijsturen (alleen het niet-tactische deel)
            if variant == "kern+archer":
                tac_eth = tac["eth"] if tac else 0.0
                eqv = b.value(px)
                want = core_target * eqv / px
                have = b.eth - tac_eth
                if abs(want - have) * px > 0.02 * eqv:
                    if want > have:
                        spend = min((want - have) * px, b.cash); b.cash -= spend; b.eth += spend * (1 - FEE) / px
                    else:
                        q = have - want; b.eth -= q; b.cash += q * px * (1 - FEE)
                    b.trades += 1
        eq.append((c["t"], b.value(px)))
    return eq, b.trades


def report(w, eq, start, trades):
    hold = w[-1]["c"] / w[start]["o"]
    peak = mdd = 0
    for _, v in eq:
        peak = max(peak, v); mdd = max(mdd, 1 - v / peak)
    return eq[-1][1], eq[-1][1] / hold, mdd, trades


VARIANTS = ["houden", "archer", "trend", "kern+trend", "kern+archer"]


def table(w, start_date, **kw):
    sd = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    start = next(i for i, x in enumerate(w) if x["t"] >= sd)
    rows = []
    for v in VARIANTS:
        eq, n = simulate(w, v, start, **kw)
        rows.append((v,) + report(w, eq, start, n))
    return rows


if __name__ == "__main__":
    w = load()
    if "robuust" in sys.argv:
        for zz in (0.20, 0.25, 0.30):
            for sma_n in (20, 30, 40):
                rows = table(w, "2021-01-01", zz=zz, sma_n=sma_n)
                print(f"zigzag {zz:.0%} SMA{sma_n}w: " + "  ".join(f"{v}={inEth:.2f}" for v, _, inEth, _, _ in rows))
    else:
        # Standaard (keuze gebruiker, 14 nov 2026): alleen 2021-nu, gesplitst in twee helften om toeval te herkennen.
        cut = next(i for i, x in enumerate(w) if x["t"] >= datetime(2024, 1, 1, tzinfo=timezone.utc))
        for label, ww, sd in [("2021 - nu", w, "2021-01-01"), ("2021 - 2023 (deel 1)", w[:cut], "2021-01-01"),
                              ("2024 - nu (deel 2)", w, "2024-01-01")]:
            rows = table(ww, sd)
            print(f"\n{label}   (in_ETH = eindwaarde tegenover houden, 1,00 = gelijk)")
            for v, x, inEth, mdd, n in rows:
                print(f"  {v:<12} in_ETH {inEth:5.2f}   max_daling {mdd:4.0%}   transacties {n}")
