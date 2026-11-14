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

## Strategie: trend op het 50-dagengemiddelde, zonder vaste kern (vanaf 14 nov 2026)
Gekozen na een backtest op 3 jaar dagdata (`research/swing_backtest.py`, uitleg in `research/archer-strategie.md`):
in beide helften en bij 40-75 dagen beter dan houden, ook met driedubbele kosten, ~1-2 trades per maand.
1. **Geen vaste kern** (keuze gebruiker, 14 nov 2026): alles volgt de trendregel. In de backtest gaf dat het
   meeste ETH op het einde, maar ook tot 30% achterstand op gewoon houden onderweg.
2. **Trend**: sloot de laatste **gesloten dagcandle boven het 50-dagengemiddelde**, dan is het doel 100% ETH;
   sloot ze **eronder**, dan 0% ETH (alles in USDC). `status` berekent dit in het blok "STRATEGIE".
3. **Bijsturen** alleen als de verdeling meer dan 5 procentpunt van het doel afwijkt, en dan in één keer naar het doel.
   Het doel verandert alleen na een dagsluiting (00:00 UTC); de meeste rondes zijn dus "niets doen".
4. Geen grenzen verleggen, geen eigen stops, geen extra trades op gevoel. Het weekbeeld en het Archer-blok zijn
   alleen context voor je uitleg.
5. Afwijken mag alleen gemotiveerd: schrijf in de ronde welke regel je niet volgt en waarom.
6. **Schaduwen**: twee schaduwportefeuilles lopen automatisch mee (bijgewerkt bij `round`): kern 50% + 30 weken,
   en kern 50% + 50 dagen.
7. **Succescriterium (vast, niet aanpassen)**: op 14 mei 2027 is de portefeuille meer dan 2 ETH waard én meer dan
   beide schaduwportefeuilles.

## Koersen
Lukt Kraken niet rechtstreeks (bv. in de Claude-cloud), dan gebruikt `trader.py` de momentopname in
`data/market.json`. Dat is toegelaten, geen fout.

## Stappen
0. `git pull --rebase origin main` (niet nodig in GitHub Actions; daar regelt de workflow git).
1. `python3 trader.py status`: marktoverzicht, ETH in detail, het blok "STRATEGIE" (doelverdeling, wat er
   bijgestuurd moet worden, schaduw en criterium) en het Archer-blok als context.
2. Lees de laatste 3 rondes in `data/state.json` om je eigen plan en niveaus te kennen.
3. Pas de regels van de strategie toe. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy ETH <USDC> "reden"` of `python3 trader.py sell ETH all|<USDC> "reden"`.
5. Altijd: `python3 trader.py round "Ronde N: analyse en plan"` (Nederlands, 2 tot 4 zinnen, concreet: dagslot
   tegenover het 50-dagengemiddelde, doelverdeling, en bij welke koers het doel bij de volgende dagsluiting omslaat).
6. `python3 trader.py export`.
7. Buiten GitHub Actions: commit `data/state.json` en `docs/data.json` als `Ronde N: <korte samenvatting>` en push naar `main`.
