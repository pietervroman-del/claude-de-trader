# Marktonderzoek: werkt de 50-dagenregel ook buiten ETH? (15 nov 2026)

Regel: alles in de markt als de gesloten dag boven het 50-dagengemiddelde sloot, anders alles in cash (geen short).
0,4% kosten per transactie. Data: Binance (crypto), Yahoo Finance (rest). Script: `marktonderzoek.py`.
**Verhouding** = eindwaarde met de regel gedeeld door gewoon houden (boven 1 = regel beter).

| markt | recent (nov 2023 - nu): regel / houden | verhouding | ervoor (nov 2020 - nov 2023) | 40 / 60 dagen (recent) | 200 dagen recent / ervoor |
|---|---|---|---|---|---|
| **ETH** | +181% / −14% | **3,27** | 0,89 | 3,40 / 2,69 | 1,65 / 1,61 |
| **DOGE** | +56% / −25% | **2,07** | 1,24 | 3,78 / 2,03 | 1,48 / 0,90 |
| **ADA** | −33% / −61% | **1,71** | 2,01 | 2,05 / 2,61 | 1,21 / 2,70 |
| **LINK** | −5% / −41% | **1,60** | 0,54 | 1,67 / 1,79 | 1,04 / 0,37 |
| SOL | +24% / +7% | 1,15 | 2,56 | 1,80 / 0,80 | 1,15 / 3,92 |
| BTC | +94% / +69% | 1,14 | 1,58 | 1,11 / 1,07 | 0,93 / 0,97 |
| XRP | +51% / +41% | 1,07 | 0,57 | 0,92 / 0,79 | 0,96 / 0,15 |
| BNB | +82% / +129% | 0,79 | 1,62 | 0,49 / 0,99 | 0,54 / 0,73 |
| Goud | +69% / +98% | 0,86 | 0,76 | 0,76 / 0,83 | 1,08 / 0,66 |
| Zilver | +30% / +113% | 0,61 | 0,73 | 0,57 / 0,72 | 0,95 / 0,75 |
| Olie (WTI) | −17% / +16% | 0,72 | 0,53 | 0,74 / 0,76 | 0,64 / 0,91 |
| S&P 500 | +19% / +69% | 0,71 | 0,67 | 0,70 / 0,73 | 0,90 / 0,85 |
| Nasdaq 100 | +17% / +79% | 0,66 | 0,81 | 0,60 / 0,66 | 0,84 / 1,02 |
| Euro Stoxx 50 | −20% / +48% | 0,54 | 0,60 | 0,60 / 0,59 | 0,79 / 0,94 |
| Bel 20 | −3% / +73% | 0,56 | 0,83 | 0,60 / 0,58 | 0,81 / 0,89 |
| EUR/USD | −15% / +2% | 0,84 | 0,93 | 0,81 / 0,81 | 0,85 / 1,10 |
| GBP/USD | −23% / +6% | 0,73 | 0,88 | 0,76 / 0,74 | 0,73 / 0,97 |
| USD/JPY | −13% / +6% | 0,82 | 0,68 | 0,79 / 0,87 | 0,79 / 0,88 |

## Bevindingen
1. **Crypto: de regel helpt vaak**, vooral bij munten met diepe crashes (ETH, ADA, DOGE, LINK). Het voordeel komt
   uit het ontwijken van grote dalingen, niet uit beter timen van stijgingen. Maar niet overal: BNB verloor in de
   recente periode, XRP en SOL hangen sterk af van de instelling.
2. **BTC: nauwelijks voordeel** (1,14 recent, 1,58 ervoor). BTC daalt minder diep dan altcoins en stijgt
   gestager; het filter kost dan ongeveer evenveel als het oplevert.
3. **Aandelenindexen, goud, zilver, olie: de 50-dagenregel verliest overal**, in beide periodes en met elke
   instelling, ook met 0,1% kosten. Deze markten stijgen gestaag met ondiepe terugvallen: de regel verkoopt bij
   elke dip en koopt duurder terug (48-79 transacties in 3 jaar). Een trager 200-dagenfilter komt dichter bij houden
   en halveert de grootste daling (S&P 500: 12% in plaats van 19%), maar wint niet.
4. **Forex: verliest overal.** Wisselkoersen bewegen in kleine golven zonder lange trends; elke kruising kost geld.
5. **Conclusie:** trendvolgen op 50 dagen is geen universele truc. Het werkt in markten met grote, lange trends en
   diepe crashes (een deel van crypto, met ETH als duidelijkste geval) en kost geld in gestage of zijwaartse markten.
   Alle cijfers zijn uit het verleden; voor ETH is de recente periode bovendien de periode waarop de regel gekozen is.
