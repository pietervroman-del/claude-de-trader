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

## Strategie: de Archer-methode (vanaf 14 nov 2026)
Je volgt de methode van de podcast *Mind to Invest*, uitgewerkt in `research/archer-strategie.md`.
`status` berekent ze voor je in het blok "Archer-methode". Kern:
1. **Alleen gesloten week- en maandcandles** beslissen over in- en uitstappen. Tussen weeksluitingen in (de meeste
   rondes) verandert er dus niets aan de signalen; dan controleer je alleen of stop of doel geraakt is.
   Niet reageren op dagbewegingen, nieuws of RSI alleen.
2. **Structuur**: hogere toppen en bodems = bullish; een ommekeer telt pas na een weekslot boven de laatste lagere top.
   Een weekslot onder de laatste bodem van de structuur = structuur kapot.
3. **Bijkopen** (signaal A): na een hogere top, een **groene weekcandle** die sluit in de Fibonacci-koopzone
   (61,8%-78,6% van de laatste impuls) en minstens **3x winst tegenover risico** tot doel 1. Geen bodems prikken in rode candles.
   Gespreid instappen mag (bv. de helft op het signaal, de rest na bevestiging).
4. **Plan vastleggen bij elke positiewijziging**: `python3 trader.py plan <stop> <doel1> <doel2> "reden"`.
   Stop onder de zone (88,6%), doel 1 = de -0,27-extensie, doel 2 = de -0,618-extensie.
5. **Uitvoeren zonder twijfel**: stop geraakt -> ETH verkopen volgens plan. Doel 1 geraakt -> de helft van de
   ETH-winstpositie verkopen en de stop naar het instapniveau. Doel 2 of een weekslot onder de laatste hogere bodem ->
   de rest verkopen. Grenzen niet verleggen om een verlies te vermijden.
6. Je mag gemotiveerd afwijken, maar schrijf dan expliciet in de ronde welke regel je niet volgt en waarom.

## Koersen
Lukt Kraken niet rechtstreeks (bv. in de Claude-cloud), dan gebruikt `trader.py` de momentopname in
`data/market.json`. Dat is toegelaten, geen fout.

## Stappen
0. `git pull --rebase origin main` (niet nodig in GitHub Actions; daar regelt de workflow git).
1. `python3 trader.py status`: marktoverzicht, ETH in detail, het Archer-blok (maand/week, structuur, Fibonacci,
   signalen) en je huidige plan met stop en doelen.
2. Lees de laatste 3 rondes in `data/state.json` om je eigen plan en niveaus te kennen.
3. Pas de Archer-regels toe. Niets doen is ook een beslissing; overtraden kost fees.
4. Trades: `python3 trader.py buy ETH <USDC> "reden"` of `python3 trader.py sell ETH all|<USDC> "reden"`,
   daarna het plan bijwerken met `python3 trader.py plan ...`.
5. Altijd: `python3 trader.py round "Ronde N: analyse en plan"` (Nederlands, 2 tot 4 zinnen, concreet: welk
   Archer-signaal, niveaus in USDC en wat er bij de volgende weeksluiting moet gebeuren).
6. `python3 trader.py export`.
7. Buiten GitHub Actions: commit `data/state.json` en `docs/data.json` als `Ronde N: <korte samenvatting>` en push naar `main`.
