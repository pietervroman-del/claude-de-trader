"""Kunnen we de valse signalen (korte verliestrades) van de 50-dagenregel wegfilteren?

Filters met vooraf gekozen waarden, getest binnen de periode waarop de regel gekozen werd (ETH, nov 2023 - nu)
én op data die nooit gebruikt is (ETH 2018 - nov 2023, BTC 2018 - nu en BTC nov 2023 - nu).
Kern 0%: alles in de munt of alles in cash. Fee 0,4%. Uitvoering aan het dagslot.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

FEE, N = 0.004, 50


def load(fn):
    rows = json.loads(Path(__file__).with_name(fn).read_text())[:-1]
    return [(datetime.fromtimestamp(r[0], timezone.utc), r[4]) for r in rows]


def run(d, start, end, filt):
    cl = [c for _, c in d]
    i0 = next(i for i, (t, _) in enumerate(d) if t >= start)
    i1 = next((i for i, (t, _) in enumerate(d) if t >= end), len(d))
    sma = lambda i: sum(cl[i - N + 1:i + 1]) / N
    cash, coin, inpos, trades, wins = 1.0, 0.0, False, 0, 0
    entry = 0
    for i in range(i0, i1):
        px, m = cl[i], sma(i)
        if filt == "geen":
            buy, sell = px > m, px < m
        elif filt == "buffer 2%":
            buy, sell = px > m * 1.02, px < m * 0.98
        elif filt == "2 dagen bevestiging":
            buy = px > m and cl[i - 1] > sma(i - 1)
            sell = px < m and cl[i - 1] < sma(i - 1)
        elif filt == "gemiddelde moet stijgen":
            buy, sell = px > m and m > sma(i - 10), px < m
        if not inpos and buy:
            coin = cash * (1 - FEE) / px; cash = 0; inpos = True; trades += 1; entry = px
        elif inpos and sell:
            cash = coin * px * (1 - FEE); coin = 0; inpos = False
            wins += px * (1 - FEE) ** 2 > entry
    end_v = cash + coin * cl[i1 - 1]
    hold = cl[i1 - 1] / cl[i0]
    return end_v / hold, trades, wins


SETS = [
    ("ETH nov 2023 - nu (gekozen periode)", "ethusdt_daily_lang.json", datetime(2023, 11, 15), datetime(2100, 1, 1)),
    ("ETH 2018 - nov 2023 (nieuw)", "ethusdt_daily_lang.json", datetime(2018, 1, 1), datetime(2023, 11, 15)),
    ("BTC nov 2023 - nu (nieuw)", "btcusdt_daily_lang.json", datetime(2023, 11, 15), datetime(2100, 1, 1)),
    ("BTC 2018 - nov 2023 (nieuw)", "btcusdt_daily_lang.json", datetime(2018, 1, 1), datetime(2023, 11, 15)),
]
FILTERS = ["geen", "buffer 2%", "2 dagen bevestiging", "gemiddelde moet stijgen"]

if __name__ == "__main__":
    data = {fn: load(fn) for _, fn, _, _ in SETS}
    print("Eindwaarde tegenover houden (1,00 = gelijk) | aantal aankopen | waarvan winstgevend")
    for label, fn, s, e in SETS:
        print(f"\n{label}")
        for f in FILTERS:
            r, n, w = run(data[fn], s.replace(tzinfo=timezone.utc), e.replace(tzinfo=timezone.utc), f)
            print(f"  {f:<26} {r:5.2f}   {n:>3} aankopen   {w:>3} winst ({w / max(n, 1):.0%})")
