"""Claude de Trader - paper trading engine (virtueel geld, echte Kraken-koersen).

Gebruik:
  python trader.py init 2 0.6                   nieuw spel: start met 2 ETH, waarvan 60% als ETH en 40% in USDC
  python trader.py status                       koersen, 24u/7d/30d, SMA's, RSI, portefeuille
  python trader.py buy  ETH 200 "reden"         koop ETH voor 200 USDC
  python trader.py sell ETH all "reden"         verkoop alle ETH (of een USDC-bedrag)
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
        "trades": s["trades"], "rounds": s["rounds"],
    }
    PUBLIC.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"docs/data.json geschreven (waarde {v:.2f} {QUOTE})")


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
    snap = {"time": now(), "tickers": live_tickers(), "weekly": {c: live_weekly(p) for c, p in PAIRS.items()}}
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
    else:
        raise SystemExit(f"Onbekend commando {cmd}")


if __name__ == "__main__":
    main(sys.argv)
