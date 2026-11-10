"""Stuurt een gsm-melding (ntfy) voor elke trade die sinds de vorige push in data/state.json bijkwam.

Gebruik (in GitHub Actions): python3 notify.py <oude-commit> <topic>
"""
import json
import subprocess
import sys
import urllib.request

SITE = "https://pietervroman-del.github.io/claude-de-trader/"


def state_at(ref):
    try:
        out = subprocess.run(["git", "show", f"{ref}:data/state.json"], capture_output=True, check=True)
        return json.loads(out.stdout.decode("utf-8-sig"))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {"trades": []}


def eur(x):
    return "€" + f"{x:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def send(topic, title, message, tags):
    body = json.dumps({"topic": topic, "title": title, "message": message, "tags": tags,
                       "click": SITE, "priority": 4}).encode("utf-8")
    req = urllib.request.Request("https://ntfy.sh/", data=body, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


def main(before, topic):
    old_ids = {t["id"] for t in state_at(before)["trades"]}
    new = state_at("HEAD")
    last = new["rounds"][-1] if new.get("rounds") else None
    for t in new["trades"]:
        if t["id"] in old_ids or t.get("fee") == 0:  # fee 0 = startpositie van een nieuw spel
            continue
        side = "KOOP" if t["side"] == "buy" else "VERKOOP"
        msg = f"{eur(t['eur'])} aan {eur(t['price'])}\n{t['reason']}"
        if last:
            msg += f"\n\nPortefeuille {eur(last['value'])} · benchmark {eur(last['benchmark'])}"
        send(topic, f"Claude de Trader: {side} {t['coin']}", msg,
             ["chart_with_upwards_trend"] if t["side"] == "buy" else ["chart_with_downwards_trend"])
        print("melding verstuurd:", side, t["coin"], t["eur"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
