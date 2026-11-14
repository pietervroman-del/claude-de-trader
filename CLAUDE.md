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

## Strategie: kern + trend (vanaf 14 nov 2026)
Gekozen na een backtest op ETH-weekdata 2017-2026 (`research/hybride_backtest.py`, uitleg in
`research/archer-strategie.md`): deze variant deed in beide helften van die periode beter dan houden, ook met andere
instellingen, met zo'n 3 transacties per jaar. Archer puur bleef ver achter.
1. **Kern**: 50% van de portefeuille blijft altijd ETH. Nooit verkopen.
2. **Trend**: sluit de laatste gesloten weekcandle **boven het 30-wekengemiddelde**, dan is het doel 100% ETH;
   sluit ze **eronder**, dan 50% ETH en 50% USDC. `status` berekent dit in het blok "STRATEGIE kern + trend".
3. **Bijsturen** alleen als de verdeling meer dan 5 procentpunt van het doel afwijkt, en dan in één keer naar het doel.
   De trend verandert alleen bij een weeksluiting; de meeste rondes zijn dus "niets doen".
4. **Archer-blok** (structuur, Fibonacci-zones) is alleen nog context in je analyse. Geen Archer-stops of -plannen meer:
   die zouden de kern verkopen. Wis een bestaand plan met `python3 trader.py plan wis`.
5. Afwijken van deze regels mag alleen gemotiveerd: schrijf in de ronde welke regel je niet volgt en waarom.

## Koersen
Lukt Kraken niet rechtstreeks (bv. in de Claude-cloud), dan gebruikt `trader.py` de momentopname in
`data/market.json`. Dat is toegelaten, geen fout.

## Stappen
0. `git pull --rebase origin main` (niet nodig in GitHub Actions; daar regelt de workflow git).
1. `python3 trader.py status`: marktoverzicht, ETH in detail, het blok "STRATEGIE kern + trend" (doelverdeling en
   wat er bijgestuurd moet worden) en het Archer-blok als context.
2. Lees de laatste 3 rondes in `data/state.json` om je eigen plan en niveaus te kennen.
3. Pas de regels van kern + trend toe. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy ETH <USDC> "reden"` of `python3 trader.py sell ETH all|<USDC> "reden"`.
5. Altijd: `python3 trader.py round "Ronde N: analyse en plan"` (Nederlands, 2 tot 4 zinnen, concreet: weekslot
   tegenover het 30-wekengemiddelde, doelverdeling, en wat er bij de volgende weeksluiting kan veranderen).
6. `python3 trader.py export`.
7. Buiten GitHub Actions: commit `data/state.json` en `docs/data.json` als `Ronde N: <korte samenvatting>` en push naar `main`.
