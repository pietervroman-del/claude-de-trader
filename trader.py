"""Claude de Trader - paper trading engine (virtueel geld, echte Kraken-koersen).

Gebruik:
  python trader.py init 2 0.6                   nieuw spel: start met 2 ETH, waarvan 60% als ETH en 40% in USDC
  python trader.py status                       koersen, 24u/7d/30d, SMA's, RSI, portefeuille
  python trader.py buy  ETH 200 "reden"         koop ETH voor 200 USDC
  python trader.py sell ETH all "reden"         verkoop alle ETH (of een USDC-bedrag)
  python trader.py plan 1640 3150 3600 "reden"  leg stop, doel 1 en doel 2 vast (plan wis = geen plan)
  python trader.py round "analyse en plan"      log een ronde (ook zonder trade)
  python trader.py export                       schrijf docs/data.json voor het dashboard
  python trader.py snapshot                     schrijf data/market.json (draait in GitHub Actions)
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data" / "state.json"
PUBLIC = ROOT / "docs" / "data.json"
MARKET = ROOT / "data" / "market.json"
FEE = 0.004  # Kraken taker fee voor kleine volumes
QUOTE = "USDC"
TRADABLE = ("ETH",)  # alleen hiermee mag gehandeld worden; de rest is enkel om de markt te lezen
TRADE_PAIRS = {"ETH": "ETHUSDC"}  # het paar waarop effectief "gehandeld" wordt

# marktoverzicht in USD (praktisch gelijk aan USDC); de indicatoren komen van deze liquide paren
PAIRS = {
    "BTC": "XXBTZUSD", "ETH": "XETHZUSD", "SOL": "SOLUSD", "XRP": "XXRPZUSD", "ADA": "ADAUSD",
    "DOGE": "XDGUSD", "LINK": "LINKUSD", "AVAX": "AVAXUSD", "DOT": "DOTUSD",
}


def kraken(path):
    req = urllib.request.Request("https://api.kraken.com/0/public/" + path,
                                 headers={"User-Agent": "claude-de-trader/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    if data.get("error"):
        raise SystemExit("Kraken: " + ", ".join(data["error"]))
    return data["result"]


def live_tickers():
    pairs = {**PAIRS, **TRADE_PAIRS}  # het handelspaar vervangt de USD-koers van die munt
    res = kraken("Ticker?pair=" + ",".join(list(PAIRS.values()) + list(TRADE_PAIRS.values())))
    return {c: {"ask": float(res[p]["a"][0]), "bid": float(res[p]["b"][0]),
                "last": float(res[p]["c"][0]), "open24": float(res[p]["o"])}
            for c, p in pairs.items()}


def live_weekly(pair):
    res = kraken(f"OHLC?pair={pair}&interval=1440")
    rows = next(v for k, v in res.items() if k != "last")
    closes = [float(r[4]) for r in rows]
    gains = [max(b - a, 0) for a, b in zip(closes[-15:-1], closes[-14:])]
    losses = [max(a - b, 0) for a, b in zip(closes[-15:-1], closes[-14:])]
    rsi = 100 - 100 / (1 + sum(gains) / sum(losses)) if sum(losses) else 100.0
    return {"ch7": (closes[-1] / closes[-8] - 1) * 100, "ch30": (closes[-1] / closes[-31] - 1) * 100,
            "sma7": sum(closes[-7:]) / 7, "sma30": sum(closes[-30:]) / 30, "rsi14": rsi,
            "high30": max(float(r[2]) for r in rows[-30:]), "low30": min(float(r[3]) for r in rows[-30:])}


# Niet elke omgeving mag Kraken bereiken (de Claude-cloud niet). Dan gebruiken we
# de laatste momentopname die GitHub Actions in data/market.json zet.
_snapshot = None


def snapshot():
    global _snapshot
    if _snapshot is None:
        _snapshot = json.loads(MARKET.read_text(encoding="utf-8"))
        print(f"[Kraken niet bereikbaar: koersen uit momentopname van {_snapshot['time']}]", file=sys.stderr)
    return _snapshot


def tickers():
    try:
        return live_tickers()
    except OSError:
        return snapshot()["tickers"]


def weekly(pair):
    coin = next(c for c, p in PAIRS.items() if p == pair)
    if _snapshot is not None:
        return _snapshot["weekly"][coin]
    try:
        return live_weekly(pair)
    except OSError:
        return snapshot()["weekly"][coin]


# --- Archer-methode (Mind to Invest): structuur en Fibonacci op de weekgrafiek, zie research/archer-strategie.md ---
ZIGZAG = 0.25  # een top/bodem telt pas na 25% terugkeer


def week_candles(pair):
    """Gesloten weekcandles (de lopende week valt weg: een open candle telt niet)."""
    if _snapshot is not None and "week_ohlc" in _snapshot:
        rows = _snapshot["week_ohlc"]
    else:
        try:
            res = kraken(f"OHLC?pair={pair}&interval=10080")
            rows = next(v for k, v in res.items() if k != "last")[:-1]
        except OSError:
            rows = snapshot()["week_ohlc"]
    return [{"t": datetime.fromtimestamp(r[0], timezone.utc), "o": float(r[1]), "h": float(r[2]),
             "l": float(r[3]), "c": float(r[4])} for r in rows]


def month_candles(weeks):
    """Maandcandles samengesteld uit weekcandles (benadering: week telt bij de maand waarin ze start)."""
    months = {}
    for w in weeks:
        k = (w["t"].year, w["t"].month)
        m = months.setdefault(k, {"t": w["t"], "o": w["o"], "h": w["h"], "l": w["l"], "c": w["c"]})
        m["h"], m["l"], m["c"] = max(m["h"], w["h"]), min(m["l"], w["l"]), w["c"]
    now_k = (datetime.now(timezone.utc).year, datetime.now(timezone.utc).month)
    return [m for k, m in sorted(months.items()) if k != now_k]


def zigzag(w, p=ZIGZAG):
    """Bevestigde toppen/bodems: [(index, 'H'/'L', prijs)], afwisselend."""
    out, mode, ext = [], None, 0
    for i in range(1, len(w)):
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
    return out


def archer(pair):
    w = week_candles(pair)
    piv = zigzag(w)
    highs = [x for x in piv if x[1] == "H"]; lows = [x for x in piv if x[1] == "L"]
    H1, H2, L1, L2 = highs[-2][2], highs[-1][2], lows[-2][2], lows[-1][2]
    struct = ("bullish (hogere toppen en bodems)" if H2 > H1 and L2 > L1 else
              "bearish (lagere toppen en bodems)" if H2 < H1 and L2 < L1 else
              "gemengd (" + ("hogere" if H2 > H1 else "lagere") + " top, " + ("hogere" if L2 > L1 else "lagere") + " bodem)")
    # laatste opwaartse impuls: laatste bodem vóór de laatste top
    lo = [x for x in lows if x[0] < highs[-1][0]][-1]
    R = H2 - lo[2]
    fib = {"r618": H2 - 0.618 * R, "r786": H2 - 0.786 * R, "r886": H2 - 0.886 * R,
           "x127": H2 + 0.27 * R, "x1618": H2 + 0.618 * R}
    last = w[-1]
    green = last["c"] > last["o"]
    in_zone = last["l"] <= fib["r618"] and last["c"] >= fib["r786"]
    stop = fib["r886"] * 0.99
    rr = (fib["x127"] - last["c"]) / (last["c"] - stop) if last["c"] > stop else 0
    return {"weeks": w[-4:], "months": month_candles(w)[-3:], "piv": [(w[i]["t"], k, v) for i, k, v in piv[-4:]],
            "struct": struct, "impuls": (lo[2], H2), "fib": fib, "last_high": H2, "last_low": L2,
            "signaal_A": H2 > H1 and in_zone and green and rr >= 3, "in_zone": in_zone, "hogere_top": H2 > H1, "groen": green, "rr": rr, "stop": stop,
            "signaal_B": H2 < H1 and green and last["c"] > H2}


def archer_summary():
    a = archer(PAIRS[TRADABLE[0]])
    r = lambda x: round(x, 2)
    return {"structuur": a["struct"], "impuls": [r(x) for x in a["impuls"]],
            "zone": [r(a["fib"]["r786"]), r(a["fib"]["r618"])], "stop": r(a["stop"]),
            "doel1": r(a["fib"]["x127"]), "doel2": r(a["fib"]["x1618"]),
            "laatste_week": "groen" if a["groen"] else "rood", "in_zone": a["in_zone"],
            "signaal_A": a["signaal_A"], "signaal_B": a["signaal_B"], "lagere_top": r(a["last_high"])}


def print_archer(c, tk):
    a = archer(PAIRS[c])
    kleur = lambda x: "groen" if x["c"] > x["o"] else "rood"
    print(f"\n{c} volgens de Archer-methode (weekgrafiek, enkel gesloten candles):")
    print("  Maandcandles: " + " | ".join(f"{m['t']:%b %Y} {kleur(m)} {m['o']:,.0f}->{m['c']:,.0f}" for m in a["months"]))
    print("  Weekcandles:  " + " | ".join(f"{x['t']:%d/%m} {kleur(x)} {x['c']:,.0f}" for x in a["weeks"]))
    print("  Toppen/bodems (zigzag 25%): " + ", ".join(f"{k} {v:,.0f} ({t:%b %Y})" for t, k, v in a["piv"]))
    print(f"  Structuur: {a['struct']}")
    f, (lo, hi) = a["fib"], a["impuls"]
    print(f"  Laatste impuls {lo:,.0f} -> {hi:,.0f}: koopzone 61,8% {f['r618']:,.0f} tot 78,6% {f['r786']:,.0f}, "
          f"stop onder 88,6% ~{a['stop']:,.0f}; doel 1 (-0,27) {f['x127']:,.0f}, doel 2 (-0,618) {f['x1618']:,.0f}")
    print(f"  Laatste week: {'groen' if a['groen'] else 'rood'}, {'in' if a['in_zone'] else 'niet in'} de koopzone, "
          f"winst/risico tot doel 1 bij instap nu: {a['rr']:.1f}x")
    print(f"  Signaal A (koop bij terugval na hogere top: groene week in de zone, winst >= 3x risico): "
          f"{'JA' if a['signaal_A'] else 'nee'}")
    if a["hogere_top"]:
        print(f"  Signaal B (ommekeer): al gebeurd, laatste top {a['last_high']:,.0f} ligt hoger dan de vorige")
    else:
        print(f"  Signaal B (ommekeer: groen weekslot boven lagere top {a['last_high']:,.0f}): "
              f"{'JA' if a['signaal_B'] else 'nee'}")
    print(f"  Structuur kapot bij een weekslot onder de laatste bodem {a['last_low']:,.0f}")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def load():
    return json.loads(STATE.read_text(encoding="utf-8-sig"))


def save(s):
    STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def value(s, tk):
    return s["cash"] + sum(q * tk[c]["bid"] for c, q in s["holdings"].items())


def bench(s, tk):
    return s["benchmark"]["qty"] * tk[s["benchmark"]["coin"]]["bid"]


def start_value(s):
    return s.get("start_value", s.get("start_eur"))


def cmd_status(s, tk):
    print(f"{'COIN':<5} {'PRIJS':>12} {'24u%':>8} {'7d%':>8} {'vs SMA30':>9}")
    for c, p in PAIRS.items():
        t, w = tk[c], weekly(p)
        print(f"{c:<5} {t['last']:>12,.4f} {(t['last']/t['open24']-1)*100:>8.2f} "
              f"{w['ch7']:>8.2f} {(t['last']/w['sma30']-1)*100:>8.1f}%")
    for c in TRADABLE:
        t, w = tk[c], weekly(PAIRS[c])
        print(f"\n{c} in detail: laatst {t['last']:,.2f} (bied {t['bid']:,.2f} / laat {t['ask']:,.2f})")
        print(f"  30d: {w['ch30']:+.1f}%, bereik {w['low30']:,.0f} - {w['high30']:,.0f}")
        print(f"  SMA7 {w['sma7']:,.0f} ({(t['last']/w['sma7']-1)*100:+.1f}%), "
              f"SMA30 {w['sma30']:,.0f} ({(t['last']/w['sma30']-1)*100:+.1f}%), RSI14 {w['rsi14']:.0f}")
        print_archer(c, tk)
    plan = s.get("plan")
    if plan:
        px = tk[TRADABLE[0]]["last"]
        print(f"\nHuidig plan (sinds {plan['time']}): stop {plan['stop']:,.0f}, doel 1 {plan['doel1']:,.0f}, "
              f"doel 2 {plan['doel2']:,.0f}" + ("  <<< STOP GERAAKT" if px <= plan["stop"] else "")
              + ("  <<< DOEL 1 GERAAKT" if px >= plan["doel1"] else ""))
        print(f"  Reden: {plan['reason']}")
    else:
        print("\nHuidig plan: geen (leg stop en doelen vast met `trader.py plan`)")
    print(f"\nCash: {s['cash']:.2f} {QUOTE}")
    for c, q in s["holdings"].items():
        print(f"{c}: {q:.6f} = {q * tk[c]['bid']:.2f} {QUOTE}")
    v, b = value(s, tk), bench(s, tk)
    bc = s["benchmark"]["coin"]
    print(f"Totaal: {v:.2f} {QUOTE} = {v / tk[bc]['bid']:.4f} {bc}  |  "
          f"Benchmark {s['benchmark']['qty']:g} {bc} houden: {b:.2f} {QUOTE}")
    print(f"Rondes tot nu: {len(s['rounds'])}, trades: {len(s['trades'])}")


def cmd_trade(s, tk, side, coin, amount, reason):
    coin = coin.upper()
    if coin not in TRADABLE:
        raise SystemExit(f"Handelen mag alleen in {', '.join(TRADABLE)}")
    if not reason:
        raise SystemExit("Geef een reden op")
    t = tk[coin]
    if side == "buy":
        eur = float(amount)
        if eur > s["cash"] + 0.001:
            raise SystemExit(f"Niet genoeg {QUOTE} ({s['cash']:.2f})")
        qty, price = eur * (1 - FEE) / t["ask"], t["ask"]
        s["cash"] -= eur
        s["holdings"][coin] = s["holdings"].get(coin, 0.0) + qty
    else:
        have = s["holdings"].get(coin, 0.0)
        if have <= 0:
            raise SystemExit(f"Geen {coin} in bezit")
        qty = have if amount == "all" else min(have, float(amount) / t["bid"])
        price = t["bid"]
        eur = qty * price * (1 - FEE)
        s["cash"] += eur
        left = have - qty
        if left > 1e-12:
            s["holdings"][coin] = left
        else:
            s["holdings"].pop(coin)
    trade = {"id": f"t{stamp()}{coin}", "time": now(), "side": side, "coin": coin, "qty": qty,
             "price": price, "eur": round(eur, 2), "fee": round(eur * FEE, 2), "reason": reason}
    s["trades"].append(trade)
    save(s)
    print(json.dumps(trade, ensure_ascii=False))


def cmd_round(s, tk, note):
    if not note:
        raise SystemExit("Geef een analyse op")
    r = {"id": f"r{stamp()[:12]}", "time": now(), "value": round(value(s, tk), 2),
         "benchmark": round(bench(s, tk), 2), "cash": round(s["cash"], 2),
         "positions": {c: round(q * tk[c]["bid"], 2) for c, q in s["holdings"].items()}, "note": note}
    s["rounds"].append(r)
    save(s)
    print(json.dumps(r, ensure_ascii=False))


def cmd_export(s, tk):
    v = value(s, tk)
    bc = s["benchmark"]["coin"]
    doc = {
        "start_eur": start_value(s), "started": s["started"], "updated": now(), "fee": FEE,
        "quote": s.get("quote", "EUR"), "start_qty": s["benchmark"]["qty"],
        "value_in_coin": round(v / tk[bc]["bid"], 6),
        "cash": round(s["cash"], 2), "value": round(v, 2),
        "benchmark": round(bench(s, tk), 2), "benchmark_coin": s["benchmark"]["coin"],
        "tradable": list(TRADABLE),
        "positions": [{"coin": c, "qty": q, "price": tk[c]["bid"], "eur": round(q * tk[c]["bid"], 2)}
                      for c, q in s["holdings"].items()],
        "market": [{"coin": c, "price": tk[c]["last"], "ch24": round((tk[c]["last"]/tk[c]["open24"]-1)*100, 2)}
                   for c in PAIRS],
        "trades": s["trades"], "rounds": s["rounds"], "plan": s.get("plan"),
        "archer": archer_summary(),
    }
    PUBLIC.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"docs/data.json geschreven (waarde {v:.2f} {QUOTE})")


def cmd_plan(s, args):
    """plan <stop> <doel1> <doel2> "reden"  |  plan wis "reden" """
    if args and args[0] == "wis":
        s["plan"] = None
        print("Plan gewist")
    else:
        if len(args) < 4:
            raise SystemExit('Gebruik: trader.py plan <stop> <doel1> <doel2> "reden"  of  trader.py plan wis')
        s["plan"] = {"time": now(), "stop": float(args[0]), "doel1": float(args[1]), "doel2": float(args[2]),
                     "reason": args[3]}
        print(json.dumps(s["plan"], ensure_ascii=False))
    save(s)


def cmd_init(qty, keep):
    """Nieuw spel met `qty` ETH, waarvan fractie `keep` als ETH blijft en de rest zonder fee in USDC staat."""
    if STATE.exists():
        raise SystemExit("data/state.json bestaat al; archiveer het oude spel eerst")
    coin, qty, keep = TRADABLE[0], float(qty), float(keep)
    t = tickers()[coin]
    price = t["last"]
    trades = [{"id": f"t{stamp()}{coin}0", "time": now(), "side": "buy", "coin": coin, "qty": qty,
               "price": price, "eur": round(qty * price, 2), "fee": 0,
               "reason": f"Startkapitaal volgens de spelregels: {qty:g} {coin}."}]
    cash = 0.0
    if keep < 1:
        sold = qty * (1 - keep)
        cash = sold * t["bid"]
        trades.append({"id": f"t{stamp()}{coin}1", "time": now(), "side": "sell", "coin": coin, "qty": sold,
                       "price": t["bid"], "eur": round(cash, 2), "fee": 0,
                       "reason": f"Overgenomen positie: {(1 - keep) * 100:.0f}% stond al in cash en staat nu in {QUOTE}."})
    s = {"start_value": qty * price, "quote": QUOTE, "started": now(), "cash": cash,
         "holdings": {coin: qty * keep}, "benchmark": {"coin": coin, "qty": qty, "price": price},
         "trades": trades, "rounds": []}
    STATE.parent.mkdir(exist_ok=True)
    save(s)
    print(f"Nieuw spel: {qty:g} {coin} aan {price:,.2f} {QUOTE}; {qty * keep:.4f} {coin} + {cash:.2f} {QUOTE}")


def cmd_snapshot():
    week = next(v for k, v in kraken(f"OHLC?pair={PAIRS[TRADABLE[0]]}&interval=10080").items() if k != "last")[:-1]
    snap = {"time": now(), "tickers": live_tickers(), "weekly": {c: live_weekly(p) for c, p in PAIRS.items()},
            "week_ohlc": week}
    MARKET.write_text(json.dumps(snap, indent=1) + "\n", encoding="utf-8")
    print(f"data/market.json geschreven ({snap['time']})")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "snapshot":
        return cmd_snapshot()
    if cmd == "init":
        return cmd_init(argv[2], argv[3])
    s, tk = load(), tickers()
    if cmd == "status":
        cmd_status(s, tk)
    elif cmd in ("buy", "sell"):
        if len(argv) < 5:
            raise SystemExit(f"Gebruik: trader.py {cmd} COIN BEDRAG \"reden\"")
        cmd_trade(s, tk, cmd, argv[2], argv[3], argv[4])
    elif cmd == "round":
        cmd_round(s, tk, argv[2] if len(argv) > 2 else "")
    elif cmd == "export":
        cmd_export(s, tk)
    elif cmd == "plan":
        cmd_plan(s, argv[2:])
    else:
        raise SystemExit(f"Onbekend commando {cmd}")


if __name__ == "__main__":
    main(sys.argv)
