"""Is er een handelsronde verschuldigd? Print true/false.

Een ronde is verschuldigd als het laatste geplande uur (Belgische tijd) voorbij is en er sindsdien nog
geen ronde in data/state.json staat. Zo maakt het niet uit hoe laat GitHub de geplande check start.
"""
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UREN = [(3, 0), (7, 30), (12, 0), (15, 0), (18, 0), (23, 0)]
TZ = ZoneInfo("Europe/Brussels")

nu = datetime.now(TZ)
gepland = [datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)
           for d in (nu.date(), nu.date() - timedelta(days=1)) for h, m in UREN]
laatste_uur = max(t for t in gepland if t <= nu)

rondes = json.load(open("data/state.json", encoding="utf-8-sig"))["rounds"]
laatste_ronde = (datetime.strptime(rondes[-1]["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                 if rondes else datetime.min.replace(tzinfo=timezone.utc))

print(f"nu {nu:%Y-%m-%d %H:%M %Z}, laatste gepland uur {laatste_uur:%H:%M}, "
      f"laatste ronde {laatste_ronde.astimezone(TZ):%Y-%m-%d %H:%M}", file=__import__("sys").stderr)
print("true" if laatste_ronde < laatste_uur else "false")
