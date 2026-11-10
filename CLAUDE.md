# Claude de Trader: een handelsronde (spel 2: ETH)

Papertrading-experiment met virtueel geld. Geen echt account, geen echte trades.
Spel 2 startte op 10 nov 2026 met €1000, volledig in ETH. Spel 1 (BTC/alts, €500) staat in `archive/`.
Publiek dashboard: `docs/index.html` (GitHub Pages) leest `docs/data.json`.

## Spelregels
- Handelen mag **alleen in ETH tegen euro**. Andere munten in `status` zijn er alleen om de markt te lezen.
- Spot only: geen hefboom, geen short. Je zit dus ergens tussen 0% en 100% ETH; de rest is cash.
- Kopen aan de laatkoers, verkopen aan de biedkoers, 0,4% fee per trade.
- Benchmark: de ETH van dag één gewoon laten staan. Elke trade moet beter doen dan niets doen, fees inbegrepen.

## Koersen
Lukt Kraken niet rechtstreeks (bv. in de Claude-cloud), dan gebruikt `trader.py` de momentopname in
`data/market.json`, die GitHub Actions om 07:00, 13:00 en 19:00 UTC ververst. Dat is toegelaten, geen fout.

## Stappen
0. `git pull --rebase origin main`. Is `data/market.json` ouder dan 3 uur en Kraken onbereikbaar: niet handelen,
   geen ronde loggen, melden dat de koersen verouderd zijn.
1. `python3 trader.py status`: alle munten (24u/7d, afstand tot SMA30) plus ETH in detail
   (30d-bereik, SMA7, SMA30, RSI14) en de portefeuille.
2. Lees de laatste 3 rondes in `data/state.json` om je eigen plan en niveaus te kennen.
3. Beslis zelf hoeveel ETH je wilt houden. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy ETH <EUR> "reden"` of `python3 trader.py sell ETH all|<EUR> "reden"`.
5. Altijd: `python3 trader.py round "analyse en plan"` (Nederlands, 2 tot 4 zinnen, concreet: niveaus en voorwaarden).
   Begin de tekst met `Ronde N:`.
6. `python3 trader.py export`.
7. Commit `data/state.json` en `docs/data.json` met als bericht `Ronde N: <korte samenvatting>` en push naar `main`.
   Faalt de push omdat main veranderd is: `git pull --rebase` en opnieuw pushen.
