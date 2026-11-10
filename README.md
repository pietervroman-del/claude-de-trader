# Claude de Trader

Een experiment: Claude krijgt een **virtuele €1000 in ETH** en beslist volledig zelfstandig wanneer hij ETH verkoopt
of terugkoopt, op echte Kraken-koersen. Drie keer per dag speelt Claude in GitHub Actions een ronde (`.github/workflows/ronde.yml`): markt bekijken, beslissen, de
redenering loggen. Bij elke koop of verkoop volgt een gsm-melding via ntfy. De tegenstander: de ETH van dag één gewoon laten staan.

Geen echt geld, geen echte trades, geen beleggingsadvies.

- `trader.py`: de papertrading-engine (alleen Python-standaardbibliotheek)
- `data/state.json`: kas, posities, alle trades en rondes
- `data/market.json`: koersen, ververst door GitHub Actions
- `docs/`: het publieke dashboard (GitHub Pages)
- `CLAUDE.md`: wat Claude in elke ronde doet
- `archive/`: afgelopen spellen

## Spelregels (spel 2, vanaf 10 november 2026)
- Start: €1000, volledig in ETH.
- Handelen alleen in ETH tegen euro; de andere munten dienen enkel om de markt te lezen.
- Spot only: geen hefboom, geen short.
- Kopen aan de laatkoers, verkopen aan de biedkoers, 0,40% fee per trade.

## Spel 1 (17 okt – 10 nov 2026)
€500 met vrije keuze uit 9 munten. Na 35 rondes eindigde Claude op €487,38; BTC kopen en houden stond op €458,21.
