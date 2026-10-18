# Claude de Trader

Een experiment: Claude krijgt een **virtuele €500** en handelt volledig zelfstandig in crypto, op echte Kraken-koersen.
Drie keer per dag doet een Claude cloud-routine een ronde: markt bekijken, beslissen, de redenering loggen.
De tegenstander: €500 in BTC op dag één en gewoon laten staan.

Geen echt geld, geen echte trades, geen beleggingsadvies.

- `trader.py`: de papertrading-engine (alleen Python-standaardbibliotheek)
- `data/state.json`: kas, posities, alle trades en rondes
- `docs/`: het publieke dashboard (GitHub Pages)
- `CLAUDE.md`: wat Claude in elke ronde doet

## Spelregels
- Spot only: geen hefboom, geen short.
- Munten: BTC, ETH, SOL, XRP, ADA, DOGE, LINK, AVAX, DOT.
- Kopen aan de laatkoers, verkopen aan de biedkoers, 0,40% fee per trade.
