"""Claude de Trader - paper trading engine (virtueel geld, echte Kraken-koersen).

Gebruik:
  python trader.py status                       koersen, 24u/7d, SMA30, portefeuille
  python trader.py buy  SOL 100 "reden"         koop voor EUR 100
  python trader.py sell SOL all "reden"         verkoop alles (of een EUR-bedrag)
  python trader.py round "analyse en plan"      log een ronde (ook zonder trade)
  python trader.py export                       schrijf docs/data.json voor het dashboard
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data" / "state.json"
PUBLIC = ROOT / "docs" / "data.json"
FEE = 0.004  # Kraken taker fee voor kleine volumes

PAIRS = {
    "BTC": "XXBTZEUR", "ETH": "XETHZEUR", "SOL": "SOLEUR", "XRP": "XXRPZEUR", "ADA": "ADAEUR",
    "DOGE": "XDGEUR", "LINK": "LINKEUR", "AVAX": "AVAXEUR", "DOT": "DOTEUR",
}


def kraken(path):
    req = urllib.request.Request("https://api.kraken.com/0/public/" + path,
                                 headers={"User-Agent": "claude-de-trader/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    if data.get("error"):
        raise SystemExit("Kraken: " + ", ".join(data["error"]))
    return data["result"]


def tickers():
    res = kraken("Ticker?pair=" + ",".join(PAIRS.values()))
    return {c: {"ask": float(res[p]["a"][0]), "bid": float(res[p]["b"][0]),
                "last": float(res[p]["c"][0]), "open24": float(res[p]["o"])}
            for c, p in PAIRS.items()}


def weekly(pair):
    res = kraken(f"OHLC?pair={pair}&interval=1440")
    rows = next(v for k, v in res.items() if k != "last")
    closes = [float(r[4]) for r in rows]
    return {"ch7": (closes[-1] / closes[-8] - 1) * 100, "sma30": sum(closes[-30:]) / 30}


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


def cmd_status(s, tk):
    print(f"{'COIN':<5} {'PRIJS':>12} {'24u%':>8} {'7d%':>8} {'vs SMA30':>9}")
    for c, p in PAIRS.items():
        t, w = tk[c], weekly(p)
        print(f"{c:<5} {t['last']:>12,.4f} {(t['last']/t['open24']-1)*100:>8.2f} "
              f"{w['ch7']:>8.2f} {(t['last']/w['sma30']-1)*100:>8.1f}%")
    print(f"\nCash: EUR {s['cash']:.2f}")
    for c, q in s["holdings"].items():
        print(f"{c}: {q:.6f} = EUR {q * tk[c]['bid']:.2f}")
    v, b = value(s, tk), s["benchmark"]["qty"] * tk["BTC"]["bid"]
    print(f"Totaal: EUR {v:.2f} ({(v/s['start_eur']-1)*100:+.2f}%)  |  Benchmark BTC-hold: EUR {b:.2f}")
    print(f"Rondes tot nu: {len(s['rounds'])}, trades: {len(s['trades'])}")


def cmd_trade(s, tk, side, coin, amount, reason):
    coin = coin.upper()
    if coin not in PAIRS:
        raise SystemExit(f"Onbekende coin {coin}")
    if not reason:
        raise SystemExit("Geef een reden op")
    t = tk[coin]
    if side == "buy":
        eur = float(amount)
        if eur > s["cash"] + 0.001:
            raise SystemExit(f"Niet genoeg cash ({s['cash']:.2f})")
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
         "benchmark": round(s["benchmark"]["qty"] * tk["BTC"]["bid"], 2), "cash": round(s["cash"], 2),
         "positions": {c: round(q * tk[c]["bid"], 2) for c, q in s["holdings"].items()}, "note": note}
    s["rounds"].append(r)
    save(s)
    print(json.dumps(r, ensure_ascii=False))


def cmd_export(s, tk):
    v = value(s, tk)
    doc = {
        "start_eur": s["start_eur"], "started": s["started"], "updated": now(), "fee": FEE,
        "cash": round(s["cash"], 2), "value": round(v, 2),
        "benchmark": round(s["benchmark"]["qty"] * tk["BTC"]["bid"], 2), "benchmark_coin": "BTC",
        "positions": [{"coin": c, "qty": q, "price": tk[c]["bid"], "eur": round(q * tk[c]["bid"], 2)}
                      for c, q in s["holdings"].items()],
        "market": [{"coin": c, "price": tk[c]["last"], "ch24": round((tk[c]["last"]/tk[c]["open24"]-1)*100, 2)}
                   for c in PAIRS],
        "trades": s["trades"], "rounds": s["rounds"],
    }
    PUBLIC.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"docs/data.json geschreven (waarde EUR {v:.2f})")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
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
