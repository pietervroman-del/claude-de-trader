"""Swing-strategieën voor ~1-2 trades per maand op ETH-dagcandles (Binance ETH/USDT, ~ ETH/USDC).

Doel: op het einde meer ETH dan bij gewoon houden. Elke variant heeft een vaste ETH-kern en een tactisch deel.
Alle signalen op GESLOTEN dagcandles, uitvoering aan de slotkoers, 0,4% fee per transactie.

Families (vooraf gekozen, niet op de uitkomst afgesteld):
  trend    tactisch deel in ETH boven het N-dagengemiddelde, anders USDC
  rsi      tactisch deel verkopen als RSI14 > hoog, terugkopen als RSI14 < laag
  bollinger tactisch deel verkopen bij slot boven bovenband (20d, k), terugkopen bij slot onder onderband
  band     vaste verdeling (bv. 70% ETH) en herbalanceren zodra ze meer dan X procentpunt afwijkt
  donchian tactisch deel kopen bij slot boven N-dagen-top, verkopen bij slot onder N/2-dagen-bodem
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FEE = 0.004


def load():
    rows = json.loads(Path(__file__).with_name("eth_daily_binance.json").read_text())[:-1]  # lopende dag weg
    return [{"t": datetime.fromtimestamp(r[0], timezone.utc), "o": r[1], "h": r[2], "l": r[3], "c": r[4]} for r in rows]


def sma(xs, n, i):
    return sum(xs[i - n + 1:i + 1]) / n if i >= n - 1 else None


def rsi(cl, i, n=14):
    if i < n:
        return None
    g = sum(max(cl[j] - cl[j - 1], 0) for j in range(i - n + 1, i + 1))
    l = sum(max(cl[j - 1] - cl[j], 0) for j in range(i - n + 1, i + 1))
    return 100.0 if l == 0 else 100 - 100 / (1 + g / l)


def std(xs, n, i):
    m = sma(xs, n, i)
    return (sum((x - m) ** 2 for x in xs[i - n + 1:i + 1]) / n) ** 0.5


def run(d, start, end, fam, p, core=0.5):
    """Geeft (eindwaarde in ETH tov houden, trades per maand, max daling in ETH-termen)."""
    cl = [x["c"] for x in d]
    eth, usd = 1.0, 0.0            # start volledig in ETH (1 ETH), zoals 'houden'
    tac_in = True                  # tactisch deel staat in ETH bij de start
    trades = 0
    worst = 0.0
    for i in range(start, end):
        px = cl[i]
        val = eth * px + usd
        frac = eth * px / val

        def to(target):
            nonlocal eth, usd, trades
            v = eth * px + usd
            diff = target * v - eth * px
            if abs(diff) < 0.005 * v:
                return
            trades += 1
            if diff > 0:
                usd -= diff; eth += diff * (1 - FEE) / px
            else:
                q = -diff / px; eth -= q; usd += q * px * (1 - FEE)

        if fam == "trend":
            m = sma(cl, p["n"], i)
            if m:
                want = px > m
                if want != tac_in:
                    to(1.0 if want else core); tac_in = want
        elif fam == "rsi":
            r = rsi(cl, i)
            if r is not None:
                if tac_in and r > p["hoog"]:
                    to(core); tac_in = False
                elif not tac_in and r < p["laag"]:
                    to(1.0); tac_in = True
        elif fam == "bollinger":
            if i >= 19:
                m, s = sma(cl, 20, i), std(cl, 20, i)
                if tac_in and px > m + p["k"] * s:
                    to(core); tac_in = False
                elif not tac_in and px < m - p["k"] * s:
                    to(1.0); tac_in = True
        elif fam == "band":
            if abs(frac - p["doel"]) > p["x"] or i == start:
                to(p["doel"])
        elif fam == "donchian":
            n = p["n"]
            if i >= n:
                top = max(x["h"] for x in d[i - n:i]); bot = min(x["l"] for x in d[i - n // 2:i])
                if not tac_in and px > top:
                    to(1.0); tac_in = True
                elif tac_in and px < bot:
                    to(core); tac_in = False
        hold_eth = 1.0
        worst = max(worst, 1 - (eth * px + usd) / px / hold_eth)
    v_eth = (eth * cl[end - 1] + usd) / cl[end - 1]
    months = (d[end - 1]["t"] - d[start]["t"]).days / 30.44
    return v_eth, trades / months, worst


GRID = {
    "trend": [{"n": n} for n in (20, 50, 100)],
    "rsi": [{"hoog": h, "laag": l} for h, l in ((70, 30), (75, 35), (65, 35))],
    "bollinger": [{"k": k} for k in (1.5, 2.0, 2.5)],
    "band": [{"doel": t, "x": x} for t, x in ((0.7, 0.05), (0.7, 0.10), (0.5, 0.10))],
    "donchian": [{"n": n} for n in (20, 40, 60)],
}


def idx(d, s):
    sd = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return next(i for i, x in enumerate(d) if x["t"] >= sd)


if __name__ == "__main__":
    d = load()
    a, m, e = idx(d, "2023-11-14"), idx(d, "2025-05-14"), len(d)
    print(f"ETH: {d[a]['c']:,.0f} (nov 2023) -> {d[m]['c']:,.0f} (mei 2025) -> {d[-1]['c']:,.0f} (nu)")
    print("in ETH tov houden (1,00 = gelijk) | trades/maand | slechtste achterstand op houden")
    for core in (0.5, 0.7):
        print(f"\n== kern {core:.0%}")
        for fam, ps in GRID.items():
            for p in ps:
                full = run(d, a, e, fam, p, core); h1 = run(d, a, m, fam, p, core); h2 = run(d, m, e, fam, p, core)
                tag = " ".join(f"{k}={v}" for k, v in p.items())
                print(f"  {fam:<9} {tag:<18} 3 jaar {full[0]:.2f} | deel1 {h1[0]:.2f} | deel2 {h2[0]:.2f} | "
                      f"{full[1]:.1f}/mnd | achterstand {full[2]:.0%}")
