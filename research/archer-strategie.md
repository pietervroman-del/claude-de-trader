# De Archer-strategie (Mind to Invest), vertaald naar regels voor ETH

Bron: 12 afleveringen van de podcast *Mind to Invest* (april 2025 – november 2026), automatische Spotify-transcripties.
Dit is onze lezing van hun methode, geen beleggingsadvies. Waar zij iets alleen op het scherm toonden, is de invulling
een eigen keuze (gemarkeerd met *keuze*).

## Regels
1. **Tijdframe** – van groot naar klein: 6 maanden → 3 maanden → maand → week. Nooit lager dan de weekgrafiek om te
   beleggen; de daggrafiek alleen voor detail. Een candle telt pas na de sluiting.
2. **Structuur** – hogere toppen en hogere bodems = bullish, lagere toppen en lagere bodems = bearish.
   Een ommekeer telt pas na een slot boven de laatste lagere top (of onder de laatste hogere bodem).
   Gezond: snelle impuls, trage correctie tegen de trend in. Alarm: impulsieve daling of correctie mét de trend.
3. **Fibonacci** – getrokken over de laatste impuls (bodem → top).
   Koopzone: de terugval vanaf 61,8% (*keuze*: tot 78,6%). Eerste doel: de −0,27-extensie. Tweede doel: −0,618.
4. **Instap** – alleen in een koopzone (Fibonacci, eerdere koopzone, rond getal) en pas na bevestiging:
   een bullish week- of maandkaars die in of boven de zone sluit, of een doorbraak boven de laatste lagere top.
5. **Risico** – instap, stop en doel vooraf vastleggen. Stop onder de zone (*keuze*: 0,886-retracement).
   Mogelijke winst minstens 3× het risico. Bij doel 1 de helft verkopen en de stop naar de instap.
   Rest verkopen bij een weekslot onder de laatste hogere bodem of op doel 2. Geen hefboom.
6. **Nieuws** – de grafiek is leidend; nieuws en macro alleen als context. VIX rond 35 = bijkopen (S&P).

## Backtest (`archer_backtest.py`, ETH/USD-weekcandles van Kraken, 2016 – nov 2026, fee 0,4%)
Toppen en bodems via zigzag (een top of bodem telt na X% terugkeer). Start in cash, volledige positie per trade.

| zigzag | trades | strategie sinds 2016 | ETH houden | sinds 2022: strategie / houden | max. daling strategie |
|---|---|---|---|---|---|
| 20% | 2 | ×1,52 | ×1.991 | ×1,64 / ×0,53 | 14% |
| 25% | 6 | ×0,83 | ×1.991 | ×0,55 / ×0,53 | 45% |
| 30% | 8 | ×1,08 | ×1.991 | ×0,91 / ×0,53 | 57% |
| 35% | 8 | ×0,53 | ×1.991 | ×0,74 / ×0,53 | 67% |

**Lezing:** mechanisch toegepast staat de methode bijna altijd in cash. Daardoor mist ze de grote stijgingen
(2016-17, 2020-21) volledig, maar beperkt ze de schade in dalende jaren (sinds 2022). Met 2 tot 8 trades in
11 jaar valt er statistisch niets uit te besluiten, en de uitkomst hangt sterk af van de gekozen instellingen.
Hun eigen, niet-mechanische beoordeling kan uiteraard anders uitvallen dan deze code.
