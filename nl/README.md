# Nederlandse leesbaarheidsanalyse

Leesbaarheids- en stijlanalyse voor Nederlandse manuscripten, met een analyse per hoofdstuk ter vergelijking.
Bedoeld voor romans en langere verhalen: hoe zwaar leest elk hoofdstuk, waar
zitten de lijdende vormen en tangconstructies, hoeveel dialoog staat erin, en
hoe gevarieerd is het zinsritme.

**Dit programmaatje levert statistieken op waarmee je de dynamiek en de complexiteit van je schrijven kan helpen beoordelen.** 
Er komt geen AI taalmodel aan te pas, en er gaat geen letter van uw manuscript het
internet op — alles wordt op uw eigen computer berekend. 

Wel wordt uw tekst grammaticaal ontleed, en dat gebeurt met een taalmodel van
[spaCy](https://spacy.io/usage/linguistic-features): het herkent woordsoorten en zinsdelen, zodat de stijlanalyse — lijdende
vorm, tangconstructies, naamwoordstijl — niet op zoekpatronen hoeft te steunen.
Het oordeelt niet, het ontleedt. Standaard is dat het kleine model
(`nl_core_news_sm`), dat goed werkt maar bij ingewikkelde zinnen niet helemaal
accuraat is. U kunt een nauwkeuriger model kiezen met de opdracht `taalmodel` —
er zijn er drie, van 12 MB tot 541 MB. Zie
[Een nauwkeuriger taalmodel](#een-nauwkeuriger-taalmodel).

Bekijk hier een [voorbeeldanalyse](/files/rapport_pietje_bell.pdf) (van _De Vlegeljaren van Pietje Bell_ Christiaan van Abkoude, 1914).

Dit is de Nederlandse tegenhanger van de Engelse scripts in de hoofdmap. Die
gebruiken Flesch, Flesch-Kincaid en Gunning Fog, en die zijn alle drie op het
Engels geijkt — met een lettergreepteller die `één` tot `n` reduceert en de
Engelse stomme-e-regel toepast op een taal waar de slot-e wordt uitgesproken.
Deze versie deelt daar niets mee.

---

## Snel starten

Op **macOS of Linux**, in de Terminal:

```bash
./nl/run_nl.sh
```

Op **Windows**, in PowerShell:

```powershell
.\nl\run_nl.ps1
```

Weigert PowerShell het script ("kan niet worden geladen omdat het uitvoeren van
scripts is uitgeschakeld"), start het dan als
`powershell -ExecutionPolicy Bypass -File .\nl\run_nl.ps1`, of sta lokale
scripts eenmalig toe met `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

> **De Windows-scripts zijn nog niet op Windows getest.** `run.ps1` en
> `nl/run_nl.ps1` zijn geschreven en nagelopen naast hun bash-tegenhangers, maar
> alle runs tot nu toe waren op macOS. Loopt er iets mis — het installeren van
> uv, de vraag om de map, een stap die niet start — meld het dan met de
> foutmelding erbij en uw PowerShell-versie (`$PSVersionTable.PSVersion`). De
> analyse zelf is systeemonafhankelijk en wordt door de tests gedekt; het zijn de
> startscripts die nog op een echte Windows-machine bevestigd moeten worden.

Dat geeft een menu en vraagt om de map met uw tekst. Op macOS kunt u de map
vanuit Finder op het terminalvenster slepen; op Windows klikt u in Verkenner met
Shift+rechtermuisknop op de map, kiest u "Als pad kopiëren" en plakt u dat in het
venster. De eerste keer wordt ongeveer 100 MB opgehaald (het Nederlandse
taalmodel); daarna draait alles offline.

Rechtstreeks kan ook:

```bash
./nl/run_nl.sh rapport      ~/Documenten/mijn-boek     # alles: markdown, PDF, grafieken
./nl/run_nl.sh leesbaarheid ~/Documenten/mijn-boek     # Flesch-Douma per hoofdstuk
./nl/run_nl.sh stijl        ~/Documenten/mijn-boek     # passief, tang, schrapwoorden
./nl/run_nl.sh dialoog      ~/Documenten/mijn-boek     # dialoog, consistentie, tempo
./nl/run_nl.sh woorden      ~/Documenten/mijn-boek     # moeilijke woorden, variatie

# eigen uitvoermap voor het rapport
./nl/run_nl.sh rapport ~/Documenten/mijn-boek ~/Bureaublad/voor-mijn-redacteur
```

En op Windows, met hetzelfde effect:

```powershell
.\nl\run_nl.ps1 rapport      C:\Users\u\Documenten\mijn-boek
.\nl\run_nl.ps1 leesbaarheid C:\Users\u\Documenten\mijn-boek
.\nl\run_nl.ps1 stijl        C:\Users\u\Documenten\mijn-boek
.\nl\run_nl.ps1 dialoog      C:\Users\u\Documenten\mijn-boek
.\nl\run_nl.ps1 woorden      C:\Users\u\Documenten\mijn-boek

# eigen uitvoermap voor het rapport
.\nl\run_nl.ps1 rapport C:\Users\u\Documenten\mijn-boek C:\Users\u\Bureaublad\voor-mijn-redacteur
```

Schrijf een Windows-pad voluit en gebruik dus geen `~`: PowerShell geeft die
tilde onbewerkt door, waar bash hem eerst zou hebben vervangen.

Zonder uitvoermap komt het rapport in een momentopname te staan:

```
rapporten/
  2026-08-31-1437/
    rapport.md
    rapport.pdf
    leesbaarheid.png
    dialoog_en_tempo.png
    samenvatting.json
  laatste -> 2026-08-31-1437     (snelkoppeling naar de nieuwste run)
  index.md                       (alle runs, met het verschil per run)
```

Zo kunt u na een revisieronde zien wat er is veranderd.

Op Windows wordt de snelkoppeling `laatste` alleen gemaakt als de
ontwikkelaarsmodus aanstaat — die bepaalt of een gewoon account een symbolische
koppeling mag maken. Staat hij uit, dan wordt de koppeling stilletjes
overgeslagen: de mappen met datum en tijd en `rapporten/index.md` komen er
gewoon, en u opent de nieuwste map op naam.

---

## Wat de tool met uw bestanden doet

* Leest `.md`, `.markdown`, `.txt` en `.docx`, recursief onder de opgegeven map.
* Slaat mappen over die `draft`, `klad`, `oud` of `archief` heten.
* Volgorde is alfabetisch op bestandsnaam, dus `01_`, `02_` werkt zoals u
  verwacht.
* Eén bestand is één hoofdstuk, **tenzij** er twee of meer hoofdstukkoppen in
  staan (`Hoofdstuk 3`, `Proloog`, `Epiloog`, of een markdown-kop). Dan wordt
  daarop gesplitst.
* Uit `.docx` worden ook tabellen meegenomen, en Word-koppen worden herkend —
  óók de Nederlandse stijlnamen `Kop 1` en `Kop 2`, niet alleen `Heading 1`.
* Krulapostrofs worden rechtgezet, zodat `z'n` één woord blijft. De
  aanhalingstekens `„ " " « »` blijven juist staan: die zijn nodig om uw
  dialoogconventie te herkennen.

Uw bestanden worden alleen gelezen, nooit gewijzigd.

---

## De maten

Per maat: wat het meet, waar het vandaan komt, hoe wij het berekenen, en waar
het tekortschiet. Deze teksten staan ook in het rapport zelf, zodat een
redacteur die alleen de PDF krijgt kan nagaan waar een getal op steunt.

### Bereik en streefzones in één oogopslag

In de tabellen staat achter elke kolomkop een symbool: **↑** hoger is beter,
**↓** lager is beter, **•** geen betere kant.

| Maat | Typisch bereik | Beter | Streefzone (fictie) | Herkomst zone |
|---|---|---|---|---|
| Flesch-Douma | 0–100, kan erbuiten | ↑ | 60–80 | banden gepubliceerd, fictiezone van ons |
| Leesindex A | 0–100, kan erbuiten | ↑ | 55–75 | van ons |
| Fog-NL | 2–12 | ↓ | 3–7 | van ons |
| Moeilijke woorden | 0–100 % | ↓ | 1–5 % | van ons |
| TTR | 0–1 | ↑ | *geen streefwaarde* | — |
| MTLD | 10–200 | ↑ | 60–120 | van ons |
| Lijdende vorm | 0–100 % | ↓ | 5–15 % | van ons |
| Tangconstructies | 0–100 % | ↓ | 0–10 % | van ons |
| Naamwoordstijl /1000 | 0–20 | ↓ | 0–3 | van ons |
| Schrapwoorden /1000 | 0–40 | ↓ | 5–15 | van ons |
| Dialoogaandeel | 0–100 % | • | *geen streefwaarde* — genreafhankelijk | — |
| Zinsritme (spreiding) | 0–15 | ↑ | *geen streefwaarde* | — |
| Woorden per zin | 5–30 | ↓ | 10–18 | van ons |

Twee dingen om hier scherp te houden.

**Niet elke maat heeft een betere kant.** Dialoogaandeel is genreafhankelijk —
een dialoogrijke thriller is niet beter of slechter dan een introspectieve
roman. Bij die maten staat er letterlijk dat er geen streefwaarde is, in plaats
van een verzonnen getal.

**De meeste streefzones zijn van ons.** De interpretatiebanden van Flesch zijn
gepubliceerd; "60–80 voor een roman" is redactionele conventie. Daarom staat er
bij elke zone waar hij vandaan komt. Ze zijn bedoeld als richtpunt, niet als
norm — en ze staan op één plek zodat u ze kunt bijstellen
(`leesbaarheid/teksten.py`, `BEREIKEN`).

Buiten de zone vallen is geen fout. Een beladen hoofdstuk mág traag lezen.

### Flesch-Douma

**Wat het meet.** Leesgemak op een schaal van ongeveer 0 (zeer moeilijk) tot
100 (zeer makkelijk), op basis van woordlengte en zinslengte.

**Bereik en streefzone.** 0–100 (kan erbuiten vallen), hoger is beter. Streefzone voor fictie 60–80. De interpretatiebanden zijn gepubliceerd; de fictiezone is onze richtlijn.

**Waar het vandaan komt.** Rudolf Flesch publiceerde in 1948 de *Reading
Ease*-formule voor het Engels. Die is niet zomaar overdraagbaar: Nederlandse
woorden zijn gemiddeld langer, dus de Engelse gewichten geven stelselmatig te
lage scores. **W.H. Douma**, landbouwsocioloog aan de Landbouwhogeschool
Wageningen, herijkte de formule in **1960** op Nederlands materiaal in *De
leesbaarheid van landbouwbladen* (Bulletin 17, Afd. Sociologie en Sociografie).
Het resultaat is sindsdien de meest gebruikte Nederlandse leesbaarheidsmaat, en
zit onder de motorkap van vrijwel elke Nederlandse "leesbaarheidsscore".

```
Flesch-Douma = 206,84 − 0,77 × (lettergrepen per 100 woorden)
                      − 0,93 × (woorden per zin)
```

**Hoe wij het berekenen.** Zinnen en woorden komen uit de spaCy-pijplijn voor
het Nederlands, aangevuld met een lijst Nederlandse afkortingen zodat `bijv.`
en `d.w.z.` geen zinseinde worden. Lettergrepen worden geteld zoals hieronder
beschreven.

**Beperkingen.** Meet alleen oppervlaktekenmerken. Twee teksten met dezelfde
woord- en zinslengte krijgen dezelfde score, ook als de ene helder is en de
andere onnavolgbaar. Geijkt op zakelijke tekst, niet op fictie.

### Leesindex A

**Wat het meet.** Een tweede leesgemakmaat. Hoger is makkelijker.

**Bereik en streefzone.** 0–100 (kan erbuiten vallen), hoger is beter. Streefzone voor fictie 55–75 (onze richtlijn).

**Waar het vandaan komt.** **R.H.M. Brouwer**, "Onderzoek naar de
leesmoeilijkheid van Nederlands proza", *Pedagogische Studiën* 40 (**1963**).
Onafhankelijk van Douma geijkt, en jarenlang gebruikt als basis voor het bepalen
van **AVI-niveaus** in het Nederlandse basisonderwijs.

```
Leesindex A = 195 − 67 × (lettergrepen per woord) − 2 × (woorden per zin)
```

**Hoe wij het berekenen.** Dezelfde tellingen als Flesch-Douma. We tonen beide
maten naast elkaar omdat ze op verschillend materiaal zijn geijkt:
landbouwbladen tegenover proza.

**Beperkingen.** Zelfde bezwaar als Flesch-Douma. Lopen de twee voor een
hoofdstuk uiteen, dan bewegen woordlengte en zinslengte tegen elkaar in — korte
zinnen met lange woorden, of andersom. Dat verschil is zelf het signaal.

### Fog-NL

**Wat het meet.** Zinslengte en moeilijke woorden in één getal. Lager is
toegankelijker.

**Bereik en streefzone.** 2–12, lager is beter. Streefzone voor fictie 3–7 (onze richtlijn — net als de maat zelf).

**Waar het vandaan komt.** ⚠️ **Geen gepubliceerde maat — dit is een bewerking
van ons.** De vorm komt van Gunning Fog, maar de definitie van "moeilijk woord"
is vervangen. Gunning Fog rekent elk woord van drie lettergrepen of meer als
moeilijk, en dat is voor het Nederlands onbruikbaar: `ziekenhuisopname` is zes
lettergrepen en voor iedere lezer meteen duidelijk. Wij gebruiken in plaats
daarvan het frequentiepercentage hieronder.

```
Fog-NL = 0,4 × ((woorden per zin) + 100 × moeilijkwoordpercentage)
```

**Beperkingen.** Niet vergelijkbaar met gepubliceerde Fog-scores. Bruikbaar om
hoofdstukken onderling te vergelijken, niet als absoluut cijfer.

### Moeilijke woorden

**Wat het meet.** Het percentage woorden dat in het Nederlands zelden voorkomt.

**Bereik en streefzone.** 0–100 %, lager is beter. Streefzone voor fictie 1–5 % (onze richtlijn).

**Waar het vandaan komt.** De **Zipf-schaal** van **van Heuven, Mandera,
Keuleers & Brysbaert (2014)**, ingevoerd bij SUBTLEX-UK: een logaritmische
frequentiemaat waarop 1 ongeveer 0,01 voorkomen per miljoen woorden is en 7
ongeveer 100.000 per miljoen. De cijfers komen uit de bibliotheek `wordfreq`,
die voor het Nederlands onder meer Wikipedia, ondertitels, nieuws, boeken en
webtekst samenvoegt.

**Hoe wij het berekenen.** Een woord heet moeilijk onder **Zipf 3,0**.
Eigennamen en getallen tellen niet mee: over een personagenaam struikelt
niemand, en anders zou elk verzonnen plaatsnaampje het percentage opblazen.

Het belangrijkste onderdeel is de **samenstellingscorrectie**. Een zeldzaam
woord telt alsnog niet als moeilijk wanneer het uiteenvalt in delen die
allemaal alledaags zijn. Dit is precies het geval waarop de lettergreepregel
stukloopt:

| woord | Zipf | valt uiteen in | oordeel |
|---|---|---|---|
| `ziekenhuisopname` | 2,71 | ziekenhuis (5,06) + opname (4,41) | gewoon |
| `vergunningsaanvraag` | 2,09 | vergunning (4,15) + aanvraag (4,35) | gewoon |
| `koffiezetapparaat` | 2,71 | koffie + zet + apparaat | gewoon |
| `melancholie` | 2,91 | valt nergens in uiteen | **moeilijk** |
| `obstinaat` | 1,32 | valt nergens in uiteen | **moeilijk** |

De tussenklanken `-s-`, `-en-`, `-e-`, `-er-` en `-n-` worden herkend
(`vergunning|s|aanvraag`). Achtervoegsels als `-ing`, `-heid` en `-ling` zijn
uitgesloten als zelfstandig deel, zodat `stalling` niet als `stal + ling` wordt
weggeredeneerd.

**Beperkingen.** De frequentielijst is **bevroren sinds september 2024**: de
maker heeft het project stopgezet omdat door generatieve AI gegenereerde tekst
de webbronnen had vervuild. Voor ons is dat eerder een voordeel — de cijfers
liggen vast en zijn dus tussen runs vergelijkbaar — maar recent taalgebruik
ontbreekt. De samenstellingssplitsing is een heuristiek en zit er soms naast:
`weemoed` valt uiteen in `wee` + `moed` en telt daardoor als gewoon.

### Woordvariatie (MTLD en TTR)

**Wat het meet.** Hoe gevarieerd de woordkeus is. Hoger is gevarieerder.

**Bereik en streefzone.** TTR 0–1 en MTLD 10–200, hoger is gevarieerder. Voor MTLD 60–120 (onze richtlijn); voor TTR géén streefwaarde, omdat hij vanzelf daalt bij langere hoofdstukken.

**Waar het vandaan komt.** MTLD is de *Measure of Textual Lexical Diversity*
van **McCarthy & Jarvis**. TTR (type-token ratio) is simpelweg het aandeel
unieke woorden.

**Hoe wij het berekenen.** Over **lemma's**, niet over woordvormen: het
Nederlands verbuigt te veel om `liep` en `lopen` als twee verschillende woorden
te tellen. MTLD wordt in **beide richtingen** berekend en gemiddeld, zoals het
gepubliceerde algoritme voorschrijft. (De Engelse versie in `read_stats.py` doet
alleen de voorwaartse doorloop en wijkt daarmee af.)

**Beperkingen.** TTR daalt vanzelf naarmate een tekst langer wordt en is daardoor
tussen hoofdstukken van ongelijke lengte slecht vergelijkbaar. MTLD is daar juist
voor bedoeld; gebruik die als u hoofdstukken naast elkaar legt.

### Lijdende vorm

**Wat het meet.** Het percentage zinnen in de lijdende vorm: *de brief werd
ondertekend*.

**Bereik en streefzone.** 0–100 % van de zinnen, lager is meestal beter. Streefzone voor fictie 5–15 % (onze richtlijn). Nul is geen doel: soms is de lijdende vorm precies goed.

**Waar het vandaan komt.** **Genootschap Onze Taal**, Taalloket, thema
*duidelijk schrijven*. Belangrijk: Onze Taal ontraadt de lijdende vorm **niet**
categorisch. Hij is functioneel wanneer de handelende persoon er niet toe doet
of onbekend is.

**Hoe wij het berekenen.** Via het dependency-label `aux:pass` in het spaCy-model
voor het Nederlands. We melden apart hoeveel van die zinnen **geen handelende
persoon** noemen (geen "door wie"), want dat is het geval waarin de lijdende vorm
iets verbergt.

**Beperkingen.** Signalering, geen fout. In fictie is de lijdende vorm vaak een
bewuste keuze — afstandelijkheid, een personage dat overkomt wat het overkomt.
Het kleine taalmodel zit er bij ingewikkelde zinnen soms naast.

### Tangconstructies

**Wat het meet.** Het percentage zinnen waarin woorden die bij elkaar horen ver
uit elkaar staan, zodat de lezer het begin moet vasthouden tot het eind.

**Bereik en streefzone.** 0–100 % van de zinnen, lager is beter. Streefzone voor fictie 0–10 % (onze richtlijn).

**Waar het vandaan komt.** **Genootschap Onze Taal** en **Taaladvies.net**, de
adviesdienst van de **Nederlandse Taalunie**. Zij omschrijven een tangconstructie
als een te grote afstand tussen bij elkaar horende zinsdelen, en noemen daarbij
drie gevallen:

1. tussen de delen van een **scheidbaar werkwoord** — *hij **belde** zijn moeder
   na een lange, vermoeiende en rampzalige dag **op***;
2. tussen **hulpwerkwoord en hoofdwerkwoord**;
3. tussen **lidwoord en zelfstandig naamwoord**.

**Hoe wij het berekenen.** Precies die drie relaties worden gemeten
(`compound:prt`, `aux`, `det`), niet lange afstanden in het algemeen. De grens
ligt op **8 woorden**. Onze Taal noemt geen getal — "te groot" is een
leesoordeel — dus die drempel is van ons en is aanpasbaar.

**Beperkingen.** Een lange tussenzin is niet altijd fout; soms is het ritme. De
drempel is een keuze, geen norm.

### Naamwoordstijl

**Wat het meet.** Een werkwoord vervangen door een naamwoord plus hulpwerkwoord:
*een beslissing nemen* in plaats van *beslissen*.

**Bereik en streefzone.** 0–20 per 1000 woorden, lager is beter. Streefzone voor fictie 0–3 (onze richtlijn).

**Waar het vandaan komt.** **Genootschap Onze Taal**, Taalloket. Zij beschrijven
het effect als afstandelijker, waardoor de boodschap wordt verzacht — soms
ongewenst, soms precies de bedoeling.

**Hoe wij het berekenen.** Zelfstandige naamwoorden op `-ing`, `-atie`, `-heid`,
`-iteit`, `-isme` en dergelijke, maar **alleen** wanneer ze aan een licht
werkwoord hangen (`doen`, `maken`, `geven`, `nemen`, `plaatsvinden`). *De
beslissing viel haar zwaar* telt dus niet: daar is het naamwoord gewoon het
onderwerp en valt er niets te vereenvoudigen.

**Beperkingen.** In fictie kan afstandelijkheid het doel zijn, bijvoorbeeld in
ambtelijke dialoog. Signalering, geen fout.

### Schrapwoorden

**Wat het meet.** Stoplappen en versterkers per duizend woorden: *eigenlijk,
gewoon, echt, natuurlijk, in feite*.

**Bereik en streefzone.** 0–40 per 1000 woorden, lager is beter. Streefzone voor fictie 5–15 (onze richtlijn). Nul is geen doel — in dialoog horen stopwoorden thuis.

**Waar het vandaan komt.** ⚠️ **Geen gezaghebbende bron.** Dit is redactionele
conventie, geen taalregel. De lijst is samengesteld uit gangbaar schrijfadvies
en is de enige maat in deze tool zonder publicatie eronder.

**Hoe wij het berekenen.** Losse woorden op tokenniveau; uitdrukkingen van
meerdere woorden (*in feite*, *als het ware*) met een patroon over de zin. De
lijst staat in `leesbaarheid/teksten.py` en is bedoeld om aan te passen.

**Beperkingen.** Sterk smaakgebonden. In dialoog zijn stopwoorden vaak juist
realistisch — zo praten mensen. Lees de vindplaatsen, niet alleen het getal.

### Dialoogaandeel en consistentie

**Wat het meet.** Het percentage woorden in dialoogalinea's, welke
aanhalingsconventie u hanteert, en welke hoofdstukken daarvan afwijken.

**Bereik en streefzone.** 0–100 % van de woorden. **Geen betere kant en geen streefwaarde**: hoeveel dialoog een boek hoort te hebben, hangt volledig van genre en stem af.

**Waar het vandaan komt.** Voor dialoogopmaak bestaat **geen officiële
Nederlandse regel**, en dat is zelf de belangrijkste bevinding. **Onze Taal**:
enkele of dubbele aanhalingstekens is een kwestie van smaak, waarbij enkele
(`'…'`) tegenwoordig de voorkeur hebben omdat ze een rustiger tekstbeeld geven.
Wat wél geldt:

* wees **consequent** binnen één tekst;
* bij een citaat binnen een citaat schakelt u naar de andere soort;
* citeert u een hele zin, dan staan punt, vraag- en uitroepteken **binnen** de
  aanhalingstekens.

**Hoe wij het berekenen.** De tool legt u geen conventie op. Hij stelt eerst
vast welke u zelf gebruikt (`'…'`, `"…"`, `„…"`, `«…»`, of een dialoogstreepje)
en meldt daarna welke hoofdstukken afwijken. Meting gebeurt op alinea-niveau,
want in Nederlands proza krijgt elke spreker een eigen alinea.

**Beperkingen.** Een verteller die veel citeert telt mee als dialoog. Citaten
binnen citaten gebruiken terecht de andere soort en kunnen als afwijking
opduiken — controleer de melding voordat u iets verandert.

### Zinsritme

**Wat het meet.** Gemiddelde, mediaan, p90 en **spreiding** van de zinslengte.

**Bereik en streefzone.** Spreiding 0–15, meer variatie leest levendiger. **Geen streefwaarde** — er bestaat geen goede of foute zinslengte.

**Waar het vandaan komt.** Beschrijvende statistiek. Geen geijkte index, geen
norm, geen bron — het is gewoon het meten van uw eigen zinnen.

**Hoe wij het berekenen.** Woorden per zin. Er is bewust **geen drempelwaarde**;
u ziet alleen het verloop over de hoofdstukken. De spreiding is de
interessantste: een hoofdstuk waarin elke zin ongeveer even lang is, leest vlak,
of die zinnen nu kort of lang zijn.

**Beperkingen.** Er bestaat geen goede of foute zinslengte. Dit is materiaal om
naar te kijken, geen cijfer om te halen.

---

## Lettergrepen: hoe ze geteld worden

Alle formules hierboven staan of vallen hiermee, dus het verdient een eigen
uitleg. De aanpak is hybride, omdat de twee voor de hand liggende methodes op
verschillende plekken misgaan.

**Pyphen** breekt woorden af met **Hunspell-afbreekpatronen** — hetzelfde
formaat en algoritme dat LibreOffice, OpenOffice en Scribus gebruiken om
Nederlandse tekst te zetten. De woordenboeken komen rechtstreeks uit de
git-repository van LibreOffice; het Nederlandse bestand heet `hyph_nl_NL`. Dit
is dus niet iemands heuristiek maar de afbreektabel die in de praktijk elke
Nederlandse tekstverwerker gebruikt.

Maar de Nederlandse afbreekregels verbieden het afbreken van een losse letter,
dus pyphen telt te laag waar een lettergreep uit één klinker bestaat:

```
mooie   -> mooie      1, moet 2
idee    -> idee       1, moet 2
België  -> Bel-gië    2, moet 3
```

**Klinkerkernen tellen** lost precies die gevallen op, maar ziet niet dat een
klinkerpaar over een lettergreepgrens kan lopen:

```
museum  -> mu-seum    2, moet 3     ("eu" is hier geen tweeklank)
```

Daarom: **pyphen bepaalt de grenzen, en binnen elk fragment tellen we
klinkerkernen.** De kernenteller hoeft dan alleen nog binnen korte fragmenten te
werken. De teller kent de Nederlandse digrafen en drieklanken (`aa ee oo uu ie
oe eu ui ij ei ou au aai ooi oei eeu ieu`), past **geen** stomme-e-regel toe (de
slot-e is een uitgesproken sjwa: `hoge` = 2), en behandelt een **trema als
kernbreker**: `reünie` = 3, `coördinatie` = 5. Accenten zonder trema horen juist
bij de kern, dus `één` = 1.

Er is een gouden tabel van handmatig gecontroleerde woorden in
`tests/test_lettergrepen.py`; die draait tegen zowel de hybride teller als de
terugval, zodat afwijkingen zichtbaar blijven.

**Kanttekening.** Afbreekpunten zijn niet exact hetzelfde als fonologische
lettergrepen: de Nederlandse afbreekregels zijn deels morfologisch
(`zieken-huis-op-na-me`). Voor leesbaarheidsformules, die lettergrepen als
*benadering* van woordcomplexiteit gebruiken, is dat ruim voldoende. Het blijft
een benadering.

---

## Wat de tool niet meet

Belangrijker dan de lijst hierboven. Deze tool zegt **niets** over:

* of het verhaal werkt — plot, spanning, structuur;
* of personages geloofwaardig zijn;
* of de dialoog klinkt als mensen;
* of de tekst samenhangt, of alleen uit losse heldere zinnen bestaat;
* of iets feitelijk klopt;
* of het goed is.

Een laag cijfer is geen literair oordeel. Een hoofdstuk mag traag lezen omdat
het traag hóórt te lezen. Gebruik de cijfers om te zien wáár u moet kijken, niet
om te bepalen wat er moet gebeuren.

---

## Waarom deze formules, en wat er beter is

Eerlijk gezegd: Douma (1960) en Brouwer (1963) zijn ruim zestig jaar oud en
worden al bijna even lang bekritiseerd. Ze meten woordlengte en zinslengte, en
daarmee niet wat een tekst werkelijk moeilijk maakt — samenhang, structuur,
voorkennis, hoe ver een verwijzing van zijn antecedent staat. Die kritiek is in
het Nederlandse taalbeheersingsonderzoek uitvoerig gedocumenteerd, onder meer
door **Lentz & Jansen (2008)** en **Kraf & Pander Maat (2009)**. Ze worden nog
steeds gebruikt bij gebrek aan even eenvoudige alternatieven.

Er is een moderne opvolger: **T-Scan** en de daarop gebouwde
**LiNT**-leesbaarheidsformule (**Pander Maat e.a., 2023**) zijn de huidige stand
van zaken voor het Nederlands. Die vragen een aanzienlijk zwaardere
infrastructuur dan deze tool.

Waarom dan toch de klassiekers? Omdat ze eenvoudig, offline en per hoofdstuk
vergelijkbaar zijn — en omdat het bij fictie tóch om het **verloop** gaat, niet
om het absolute getal. Of uw hoofdstuk 7 een 62 of een 58 scoort, zegt weinig.
Dat het twaalf punten onder de rest van het boek zit, zegt wel iets.

---

## Onderliggende bronnen en licenties

| Onderdeel | Herkomst | Licentie |
|---|---|---|
| pyphen + afbreekwoordenboeken | LibreOffice-repository (`hyph_nl_NL`) | GPL 2.0+ / LGPL 2.1+ / MPL 1.1 |
| spaCy-model `nl_core_news_sm` | UD Dutch Alpino + LassySmall | CC BY-SA 4.0 |
| wordfreq | Wikipedia, ondertitels, nieuws, boeken, web | MIT (brondata wisselend) |

Alpino en Lassy zijn de standaard Nederlandse syntactische treebanks (Alpino uit
Groningen, Lassy uit het STEVIN-programma). Doordat het model
**Universal Dependencies** gebruikt, zijn labels als `aux:pass` en
`compound:prt` beschikbaar; dat is wat de stijlanalyse zonder regex mogelijk
maakt.

De licenties zijn nu niet van belang — dit is een persoonlijke repository. Zou
`nl/` ooit worden verspreid, dan is de tri-licentie van pyphen en de
afbreekwoordenboeken een bewuste keuze en geen detail.

---

## Literatuur

* Douma, W.H. (1960). *De leesbaarheid van landbouwbladen*. Bulletin 17,
  Landbouwhogeschool Wageningen. —
  [overzicht Nederlandse formules](https://kennisbank-begrijpelijketaal.nl/begripsvoorspelling/ned_formules)
* Brouwer, R.H.M. (1963). Onderzoek naar de leesmoeilijkheid van Nederlands
  proza. *Pedagogische Studiën* 40. —
  [artikel](https://pedagogischestudien.nl/article/download/16764/18235/35177)
* Lentz, L. & Jansen, C. (2008). Hoe begrijpelijk is mijn tekst? De opkomst,
  neergang en terugkeer van de leesbaarheidsformules. *Onze Taal* 77(1). —
  [publicaties Lentz](https://www.uu.nl/staff/LRLentz/Publications)
* Kraf, R. & Pander Maat, H. (2009). Leesbaarheidsonderzoek: oude problemen,
  nieuwe kansen. *Tijdschrift voor Taalbeheersing*.
* Pander Maat, H. e.a. (2023). LiNT: een leesbaarheidsformule en een
  leesbaarheidsinstrument. *Tijdschrift voor Taalbeheersing*. —
  [AUP Online](https://www.aup-online.com/content/journals/10.5117/TVT2023.3.002.MAAT)
* De Clercq, O. & Hoste, V. (2014). *Hoe meetbaar is leesbaarheid?* —
  [LT3, UGent](https://lt3.ugent.be/media/uploads/publications/2014/liberamicorum_2014_DeClercq.pdf)
* Genootschap Onze Taal, Taalloket —
  [tangconstructie](https://onzetaal.nl/taalloket/tangconstructie) ·
  [naamwoordstijl](https://onzetaal.nl/taalloket/naamwoordstijl) ·
  [duidelijk schrijven](https://onzetaal.nl/taalloket/thematisch-taaladvies/duidelijk-schrijven) ·
  [aanhalingstekens](https://onzetaal.nl/taalloket/aanhalingstekens-dubbele-aanhalingstekens)
* Taaladvies.net (Nederlandse Taalunie) —
  [tangconstructie](https://taaladvies.net/taal/advies/term/84/tangconstructie/)
* van Heuven, W.J.B., Mandera, P., Keuleers, E. & Brysbaert, M. (2014).
  SUBTLEX-UK. *Quarterly Journal of Experimental Psychology* 67(6), 1176–1190. —
  [uitleg Zipf-schaal](https://www.wellformedness.com/blog/zipf-scale/)
* wordfreq (Robyn Speer) — [repository](https://github.com/rspeer/wordfreq) ·
  [waarom de dataset bevroren is](https://github.com/rspeer/wordfreq/blob/master/SUNSET.md)
* Pyphen — [pyphen.org](https://pyphen.org/) ·
  [Hunspell-afbreekbibliotheek](https://github.com/hunspell/hyphen)
* spaCy-modellen — [explosion/spacy-models](https://github.com/explosion/spacy-models)

---

## Aanpassen

Alles wat een keuze is in plaats van een bron, staat op één plek.

| Wat | Waar | Standaard |
|---|---|---|
| Schrapwoorden en uitdrukkingen | `leesbaarheid/stijl.py` → `SCHRAPWOORDEN` | zie lijst |
| Afstand voor een tangconstructie | `leesbaarheid/stijl.py` → `TANG_DREMPEL` | 8 woorden |
| Grens voor een moeilijk woord | `leesbaarheid/woordenschat.py` → `ZIPF_DREMPEL` | 3,0 |
| Grens voor samenstellingsdelen | `leesbaarheid/woordenschat.py` → `ZIPF_DEEL_DREMPEL` | 3,3 |
| Lichte werkwoorden (naamwoordstijl) | `leesbaarheid/stijl.py` → `LICHTE_WERKWOORDEN` | doen, maken, geven … |
| Bereiken en streefzones | `leesbaarheid/teksten.py` → `BEREIKEN` | zie tabel boven |
| Alle Nederlandse rapportteksten | `leesbaarheid/teksten.py` | — |
| Taalmodel | `./nl/run_nl.sh taalmodel` (Windows: `.\nl\run_nl.ps1 taalmodel`) | `nl_core_news_sm` |

De schrapwoordenlijst is nadrukkelijk bedoeld om aan te passen: het is uw stem,
niet die van een taaladviseur. Staat er een woord in dat u bewust gebruikt,
haal het eruit. Hetzelfde geldt voor de streefzones: het zijn richtpunten, en
de meeste zijn van ons.

### Een nauwkeuriger taalmodel

De stijlanalyse — lijdende vorm, tangconstructies, naamwoordstijl — draait op
een taalmodel. Standaard is dat het kleine model, dat goed werkt maar niet
foutloos is. Een groter model herkent ingewikkelde zinnen beter.

```bash
./nl/run_nl.sh taalmodel        # laat zien wat er is en wat u gebruikt
./nl/run_nl.sh taalmodel md     # kiezen, en desgewenst meteen ophalen
```

```powershell
.\nl\run_nl.ps1 taalmodel       # op Windows, met dezelfde vragen
.\nl\run_nl.ps1 taalmodel md
```

| Model | Download | Waarvoor |
|---|---|---|
| `nl_core_news_sm` | 12 MB | standaard; snel en voor de meeste teksten prima |
| `nl_core_news_md` | 40 MB | met woordvectoren; de zinnige stap omhoog |
| `nl_core_news_lg` | 541 MB | grote vectoren; forse download, beperkte extra winst |

Voor het Nederlands bestaan alleen deze drie: er is **geen** `nl_core_news_trf`,
anders dan voor sommige andere talen. Dit is dus het hele scala.

De keuze wordt onthouden voor volgende runs. Eenmalig afwijken kan ook:

```bash
uv run --group nl python nl/analyseer.py stijl ~/Documenten/mijn-boek --model md
RS_SPACY_MODEL=nl_core_news_md ./nl/run_nl.sh stijl ~/Documenten/mijn-boek
```

In PowerShell kan een omgevingsvariabele niet vóór de opdracht op dezelfde regel;
u zet hem eerst, en dan geldt hij voor de rest van het venster:

```powershell
uv run --group nl python nl/analyseer.py stijl C:\Users\u\Documenten\mijn-boek --model md

$env:RS_SPACY_MODEL = "nl_core_news_md"
.\nl\run_nl.ps1 stijl C:\Users\u\Documenten\mijn-boek
```

> **Let op bij het vergelijken van runs.** De stijlpercentages verschuiven als u
> van model wisselt — hetzelfde hoofdstuk kan met `md` een ander passiefcijfer
> krijgen dan met `sm`. Daarom staat het gebruikte model in het rapport, in
> `samenvatting.json` en in de kolom Taalmodel van `rapporten/index.md`. Ziet u
> een sprong tussen twee runs, kijk daar eerst.

Installeren gebeurt met `uv pip install` en een vastgepinde wheel-URL, niet met
`python -m spacy download`: die laatste roept pip aan, en een door uv beheerde
omgeving heeft geen pip.

Omdat `md` en `lg` zo buiten `uv.lock` om worden geïnstalleerd, draaien de
startscripts hun `uv sync` met `--inexact`. Zonder die vlag maakt uv de omgeving
precies gelijk aan de lock en verwijdert het het model weer bij de eerstvolgende
start — dan lijkt het opgehaald, maar is het meteen weer weg. Merkt u dat een
model na installatie toch niet gevonden wordt, dan is er ergens een `uv sync`
zonder `--inexact` overheen gegaan; haal het model dan opnieuw op.

---

## Ontwikkelen

```bash
uv sync --group nl --group dev
uv run pytest                       # 198 tests
uv run pytest nl/tests/test_lettergrepen.py -v
```

Deze drie werken op Windows onveranderd; alleen het startscript verschilt
(`.\nl\run_nl.ps1` in plaats van `./nl/run_nl.sh`).

De testopstelling in `tests/fixtures/` is een klein Nederlands
voorbeeldmanuscript van vier hoofdstukken, waarin de constructies met opzet zijn
ingebouwd: hoofdstuk 2 zit vol lijdende vorm, naamwoordstijl en lange
samenstellingen, hoofdstuk 3 is bewust helder. De tests controleren dat de tool
dat verschil ook echt meet.

Bouwt u iets nieuws, houd dan de opzet aan: de bron van een maat hoort in
`teksten.py`, zodat hij vanzelf in het rapport én in deze README terechtkomt.
