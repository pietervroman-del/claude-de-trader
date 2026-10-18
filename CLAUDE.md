# Claude de Trader: een handelsronde

Papertrading-experiment met virtueel geld (start €500 op 17 okt 2026). Geen echt account, geen echte trades.
Koersen komen live van de publieke Kraken-API. Publiek dashboard: `docs/index.html` (GitHub Pages) leest `docs/data.json`.

De Claude-cloud mag api.kraken.com niet bereiken. Daarom haalt GitHub Actions (`.github/workflows/market.yml`)
om 07:00, 13:00 en 19:00 UTC de koersen op in `data/market.json`. `trader.py` gebruikt automatisch die momentopname
als Kraken onbereikbaar is; trades worden dan uitgevoerd aan die koersen. Dat is de afgesproken spelregel, geen fout.

## Stappen
0. `git pull -q origin main` om de nieuwste koersen en staat te hebben. Is `data/market.json` ouder dan 3 uur,
   handel dan niet, log geen ronde, en meld dat de koersen verouderd zijn.
1. `python3 trader.py status`: koersen, 24u/7d, afstand tot SMA30, portefeuille.
2. Lees de laatste 3 rondes en de posities in `data/state.json` om je eigen plan te kennen.
3. Beslis zelf. Volledige vrijheid binnen de spelregels: spot only, munten BTC ETH SOL XRP ADA DOGE LINK AVAX DOT, fee 0,4%.
   Doel: de benchmark (BTC kopen en houden) verslaan. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy COIN EUR "reden"` of `python3 trader.py sell COIN all|EUR "reden"`.
5. Altijd: `python3 trader.py round "analyse en plan voor volgende ronde"` (Nederlands, 2 tot 4 zinnen, concreet: niveaus, voorwaarden).
6. `python3 trader.py export`.
7. Commit `data/state.json` en `docs/data.json` met als bericht `Ronde N: <korte samenvatting>` en push naar `main`.
   Als de push faalt omdat main veranderd is: `git pull --rebase` en opnieuw pushen.
