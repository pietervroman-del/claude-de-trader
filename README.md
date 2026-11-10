# Claude de Trader

Een experiment: Claude krijgt virtueel **2 ETH** en beslist volledig zelfstandig hoeveel daarvan in ETH of in USDC
staat, op echte Kraken-koersen (paar ETH/USDC). Vier keer per dag (07:30, 12:00, 18:00 en 23:00 Belgische tijd)
speelt Claude in GitHub Actions een ronde (`.github/workflows/ronde.yml`): markt bekijken, beslissen, de redenering
loggen. Bij elke koop of verkoop volgt een gsm-melding via ntfy. De tegenstander: gewoon 2 ETH houden.

Geen echt geld, geen echte trades, geen beleggingsadvies.

- `trader.py`: de papertrading-engine (alleen Python-standaardbibliotheek)
- `data/state.json`: kas, posities, alle trades en rondes
- `docs/`: het publieke dashboard (GitHub Pages)
- `CLAUDE.md`: wat Claude in elke ronde doet
- `archive/`: afgelopen spellen

## Spelregels (vanaf 10 november 2026)
- Startkapitaal: 2 ETH. De 60/40-verdeling uit het korte euro-spel liep mee: 1,2 ETH en de rest in USDC.
- Handelen alleen ETH tegen USDC; de andere munten dienen enkel om de markt te lezen.
- Spot only: geen hefboom, geen short.
- Kopen aan de laatkoers, verkopen aan de biedkoers, 0,40% fee per trade.
- Te kloppen: gewoon 2 ETH houden.

## Eerdere spellen
- **17 okt – 10 nov 2026:** €500 met vrije keuze uit 9 munten. Na 35 rondes eindigde Claude op €487,38; BTC kopen en
  houden stond op €458,21.
- **10 nov 2026:** €1000 in ETH tegen euro, na 2 rondes omgezet naar het huidige spel.
