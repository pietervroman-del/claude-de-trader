# Claude de Trader: een handelsronde (ETH/USDC)

Papertrading-experiment met virtueel geld. Geen echt account, geen echte trades.
Huidig spel (vanaf 10 nov 2026): startkapitaal **2 ETH**, verhandeld op het Kraken-paar **ETH/USDC**.
Bij de start liep de 60/40-verdeling van het vorige spel mee: 1,2 ETH + 0,8 ETH in USDC.
Vorige spellen staan in `archive/`. Publiek dashboard: `docs/index.html` (GitHub Pages) leest `docs/data.json`.

## Spelregels
- Handelen mag **alleen ETH tegen USDC**. De andere munten in `status` (in USD) dienen alleen om de markt te lezen.
- Spot only: geen hefboom, geen short. Je zit ergens tussen 0% en 100% ETH; de rest staat in USDC.
- Kopen aan de laatkoers, verkopen aan de biedkoers, 0,4% fee per trade.
- Benchmark: gewoon 2 ETH houden. Je wint als je portefeuille meer dan 2 ETH waard is (`status` toont dat).
  Elke trade moet dus beter doen dan niets doen, fees inbegrepen.

## Koersen
Lukt Kraken niet rechtstreeks (bv. in de Claude-cloud), dan gebruikt `trader.py` de momentopname in
`data/market.json`. Dat is toegelaten, geen fout.

## Stappen
0. `git pull --rebase origin main` (niet nodig in GitHub Actions; daar regelt de workflow git).
1. `python3 trader.py status`: alle munten (24u/7d, afstand tot SMA30) plus ETH in detail
   (30d-bereik, SMA7, SMA30, RSI14) en de portefeuille, ook uitgedrukt in ETH.
2. Lees de laatste 3 rondes in `data/state.json` om je eigen plan en niveaus te kennen.
3. Beslis zelf hoeveel ETH je wilt houden. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy ETH <USDC> "reden"` of `python3 trader.py sell ETH all|<USDC> "reden"`.
5. Altijd: `python3 trader.py round "Ronde N: analyse en plan"` (Nederlands, 2 tot 4 zinnen, concreet: niveaus in USDC en voorwaarden).
6. `python3 trader.py export`.
7. Buiten GitHub Actions: commit `data/state.json` en `docs/data.json` als `Ronde N: <korte samenvatting>` en push naar `main`.
