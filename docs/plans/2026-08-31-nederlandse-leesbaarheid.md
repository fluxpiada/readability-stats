# Nederlandse leesbaarheidsanalyse — `nl/` subpackage

## Context

`readability-stats` analyseert manuscripten met Flesch, Flesch-Kincaid en Gunning Fog. Alle drie zijn op Engels gekalibreerd, en de implementatie in `read_stats.py` is dat ook — tot op het bot:

- `count_syllables()` doet `re.sub(r"[^a-z]", "", word.lower())`, dus **accenten worden gewist, niet gevouwen**: `één` → `n`, `café` → `caf`, `reünie` → `renie`. Elke Nederlandse tekst met trema's of accenten krijgt stelselmatig te lage lettergreeptellingen.
- De silent-`e`-regel (`if word.endswith("e"): syllables -= 1`) is fout voor het Nederlands, waar de slot-`e` een uitgesproken sjwa is (`hoge` = 2, niet 1).
- Digrafen en diftongen (`ij`, `eu`, `ui`, `oe`, `aai`, `eeuw`) worden niet herkend; `y` telt als klinker.
- "Complex word = 3+ lettergrepen" (Gunning Fog) is voor het Nederlands ronduit misleidend: `ziekenhuisopname` en `basisschoolleerling` zijn doorzichtige samenstellingen, geen moeilijke woorden. Fog overschat Nederlandse tekst structureel.
- `stopwords.words("english")` en NLTK `punkt` zonder taalparameter staan hard in de code.
- De typografische apostrof `’` splitst in twee tokens (`didn` + `t`), zichtbaar in `converted_txt/`.

Doel: een zelfstandige Nederlandse versie in `nl/`, met formules en stijlanalyses die voor Nederlands proza kloppen, en een rapport volledig in het Nederlands. De bestaande Engelse scripts in de repo-root blijven ongewijzigd.

**Keuzes (met gebruiker vastgesteld):** submap in deze repo · spaCy `nl_core_news_sm` toegestaan · alle vier de metriekfamilies · rapport in het Nederlands.

**Uitgangspunt bij de verantwoording hieronder:** elke maat die we rapporteren is terug te voeren op een gepubliceerde bron, en waar die bron omstreden of verouderd is, zeggen we dat in het rapport zelf. Geen zelfverzonnen indexen die als wetenschap ogen. (De bestaande Engelse `tightening_score` in `read_stats.py:241` is precies dat wél — een handgemaakte gewogen som zonder bron — en wordt in de Nederlandse versie niet overgenomen.)

---

## Structuur

Een zelfstandig pakket dat niets uit de root importeert. Eén CLI met subcommando's in plaats van tien genummerde scripts — de menu-UX van `run.sh` (Finder-drag, genummerde keuze) blijft behouden via `nl/run_nl.sh`.

```
nl/
  README.md              Nederlandse handleiding + bronvermelding
  run_nl.sh              menu-runner, zelfde drag-and-drop-UX als run.sh
  analyseer.py           CLI-entry: rapport | leesbaarheid | stijl | dialoog | tempo | woorden
  leesbaarheid/
    __init__.py
    tekst.py             md/docx → platte tekst, hoofdstukdetectie, normalisatie
    taal.py              spaCy-pipeline (singleton) + Nederlandse afkortingen
    lettergrepen.py      lettergreepteller (pyphen + eigen fallback)
    formules.py          Flesch-Douma, Leesindex A, Fog-NL
    woordenschat.py      frequentiegebaseerde moeilijkheid, samenstellingssplitsing, TTR/MTLD
    stijl.py             schrapwoorden, passief, naamwoordstijl, tangconstructies
    dialoog.py           dialoogdetectie, dialoogaandeel, zinsritme
    analyse.py           orkestratie → DataFrame + per-hoofdstuk detail
    rapport.py           Nederlands markdown + PDF + grafieken
    teksten.py           álle Nederlandse UI-strings, begrippenlijst, drempelwaarden, bronnen
  tests/
    test_lettergrepen.py gouden tabel met ~40 handmatig gecontroleerde woorden
    test_formules.py     handberekening op een vaste alinea
    fixtures/            klein Nederlands voorbeeldmanuscript (3 hoofdstukken .md + 1 .docx)
```

Alle Nederlandse teksten én de literatuurverwijzingen staan in `teksten.py`, niet verspreid door de modules — één plek om de toon van het rapport bij te stellen, en één plek waar de bronvermelding vandaan komt die onder elke rapportsectie belandt.

---

## Kern: lettergrepen (`lettergrepen.py`)

Dit is het fundament; elke formule erft de fout hiervan. Daarom als eerste bouwen en als eerste testen.

### Wat pyphen is, en waarom het gezag heeft

**Pyphen** is een pure-Python module die woorden afbreekt met **Hunspell-afbreekpatronen** — hetzelfde bestandsformaat en algoritme (afkomstig van libhnj/TeX-afbreekpatronen) dat **LibreOffice, OpenOffice en Scribus** gebruiken om Nederlandse tekst te zetten. Pyphen bundelt die woordenboeken rechtstreeks uit de git-repository van LibreOffice; het Nederlandse bestand is `hyph_nl_NL`.

Het gezag zit hem hierin: dit is niet iemands heuristiek, maar de afbreektabel die in de praktijk élke Nederlandse tekstverwerker en zetterij gebruikt. Ze wordt onderhouden in de OpenTaal-/LibreOffice-hoek, dezelfde omgeving die de Nederlandse spellingbestanden verzorgt.

**Twee kanttekeningen die in de code en het rapport horen:**

1. *Afbreekpunten zijn niet exact hetzelfde als fonologische lettergrepen.* De Nederlandse afbreekregels zijn deels **morfologisch**: samenstellingen worden op de woorddelen gesplitst (`ziekenhuis-opname`), niet strikt op klankgrepen. Voor leesbaarheidsformules — die lettergrepen als *proxy* voor woordcomplexiteit gebruiken — is dat ruim goed genoeg, en beter dan elke handgeschreven regelset. Maar we noemen het een benadering, geen waarheid.
2. *Licentie.* Pyphen staat onder een **tri-licentie GPL 2.0+ / LGPL 2.1+ / MPL 1.1**, en de meegeleverde woordenboeken komen onder GPL/LGPL/MPL uit de LibreOffice-repo. Zolang deze repo privé of persoonlijk is, speelt dat niet; zodra het ding gedistribueerd wordt, is de licentie van `nl/` een bewuste keuze en geen detail. Vastleggen in `nl/README.md`.

### Implementatie

- Primair `Pyphen(lang="nl_NL")`: `len(dic.positions(w)) + 1`.
- Fallback zonder pyphen — een echte Nederlandse heuristiek, geen Engelse:
  - klinkergroepen als één kern, met de digrafen/trigrafen `aa ee oo uu ie oe eu ui ij ei ou au aai ooi oei eeuw ieuw`;
  - **geen** silent-`e`-aftrek;
  - een **trema breekt een klinkergroep** (`reünie` = 3, `zeeën` = 3, `België` = 3) — precies waar de huidige code de tekens weggooit;
  - accenten vouwen naar de basisklinker (`één` = 1) in plaats van ze te wissen.
- `functools.lru_cache` per woord; de teller draait miljoenen keren over een manuscript.

`tests/test_lettergrepen.py` legt de gouden tabel vast: `paard`=1, `hoge`=2, `mooie`=2, `ijs`=1, `koeien`=2, `eeuwig`=2, `zeeën`=3, `reünie`=3, `België`=3, `onmiddellijk`=4, `ziekenhuisopname`=6. De test draait tegen **beide** implementaties, zodat de fallback niet stilletjes wegdrijft van pyphen.

---

## Formules (`formules.py`)

### Flesch-Douma — wat het is en waar het vandaan komt

Rudolf Flesch publiceerde in 1948/1949 de *Reading Ease*-formule voor het Engels. Die is niet zomaar overdraagbaar: Nederlandse woorden zijn gemiddeld langer en de zinsbouw verschilt, dus de Engelse gewichten geven systematisch te lage scores.

**W.H. Douma**, landbouwsocioloog aan de Landbouwhogeschool Wageningen, herijkte de formule in **1960** op Nederlands materiaal, in zijn onderzoek naar de leesbaarheid van landbouwbladen (*De leesbaarheid van landbouwbladen*, Bulletin 17, Afdeling Sociologie en Sociografie, Landbouwhogeschool Wageningen). Het resultaat, algemeen bekend als **Flesch-Douma**, is sindsdien de meest gebruikte Nederlandse leesbaarheidsmaat en is wat vrijwel elke Nederlandse "leesbaarheidsscore" in tekstverwerkers en SEO-tools onder de motorkap gebruikt.

```
Flesch-Douma = 206.84 − 0.77 × (lettergrepen per 100 woorden) − 0.93 × (woorden per zin)
```

De uitkomst loopt van ongeveer 0 (zeer moeilijk, academisch) tot 100 (zeer makkelijk). Merk op hoe dicht de gewichten bij Flesch' originele 84.6 en 1.015 liggen: het is dezelfde formule, op Nederlands bijgesteld, niet een andere.

### Leesindex A (Brouwer) — wat het is en waar het vandaan komt

**R.H.M. Brouwer** publiceerde in **1963** in *Pedagogische Studiën* (jrg. 40, "Onderzoek naar de leesmoeilijkheid van Nederlands proza") een onafhankelijk op Nederlands proza geijkte formule, de **Leesindex A**:

```
Leesindex A = 195 − 67 × (gemiddeld aantal lettergrepen per woord) − 2 × (gemiddeld aantal woorden per zin)
```

Het gezag ervan is vooral praktisch: de Leesindex A is jarenlang gebruikt als basis voor het bepalen van het **AVI-niveau** van teksten in het Nederlandse basisonderwijs. Dat maakt het een tweede, historisch stevig verankerde maat naast Douma.

We rapporteren beide bewust náást elkaar. Ze zijn onafhankelijk geijkt op verschillend materiaal (landbouwbladen versus proza); lopen ze voor een hoofdstuk uiteen, dan is dat zelf het signaal — meestal dat zinslengte en woordlengte tegengesteld bewegen.

### Fog-NL — expliciet onze aanpassing, geen gezag geclaimd

| Maat | Formule | Status |
|---|---|---|
| **Flesch-Douma** | `206.84 − 0.77·(lettergrepen/100 woorden) − 0.93·(woorden/zin)` | Douma 1960, gepubliceerd |
| **Leesindex A** | `195 − 67·(lettergrepen/woord) − 2·(woorden/zin)` | Brouwer 1963, gepubliceerd |
| **Fog-NL** | `0.4·((woorden/zin) + 100·moeilijkwoordpercentage)` | **aanpassing van ons**, zie hieronder |
| Ruwe proxies | `% woorden ≥ 4 lettergrepen`, `% woorden > 9 letters` | descriptief, geen index |

Fog-NL behoudt de vórm van Gunning Fog maar vervangt de definitie van "moeilijk woord": niet "3+ lettergrepen" (voor het Nederlands onbruikbaar door samenstellingen) maar de frequentiedrempel uit `woordenschat.py`. In het rapport staat er letterlijk bij dat dit **onze bewerking** is, niet Gunning Fog, en dus niet vergelijkbaar met gepubliceerde Fog-scores. Interpretatiebanden voor Flesch-Douma komen in `teksten.py`, met de bronvermelding erbij.

---

## Woordenschat (`woordenschat.py`)

- Moeilijkheid via **`wordfreq`** (`zipf_frequency(lemma, "nl")`), niet via lettergrepen. De **Zipf-schaal** is de psycholinguïstische standaardmaat van **van Heuven, Mandera, Keuleers & Brysbaert (2014)**, geïntroduceerd bij SUBTLEX-UK: een logaritmische schaal waarop 1 ≈ 0,01 voorkomen per miljoen woorden en 7 ≈ 100.000 per miljoen. `wordfreq` (Robyn Speer) aggregeert voor het Nederlands onder meer Wikipedia, ondertitels (SUBTLEX/OpenSubtitles), nieuws, boeken en webtekst tot één Zipf-waarde. Drempel `zipf < 3.0`, met eigennamen (spaCy `PROPN`) en getallen uitgesloten — de drempel wordt op het echte manuscript geijkt (zie verificatie), niet blind overgenomen.
  - **Relevant detail:** `wordfreq` wordt sinds september 2024 **niet meer bijgewerkt** — de maker heeft het project bewust stopgezet omdat door generatieve AI gegenereerde tekst de webbronnen heeft vervuild (`SUNSET.md` in de repo). Voor ons is dat eerder een voordeel dan een probleem: de dataset is bevroren op pre-pollutie-materiaal en dus **reproduceerbaar**. Wel de versie hard vastpinnen, zodat scores tussen runs vergelijkbaar blijven.
- **Samenstellingscorrectie** — de eigenlijke oplossing voor het Fog-probleem: bij een zeldzaam woord een gulzige splitsing op de Nederlandse verbindingsmorfemen (`-s-`, `-en-`, `-e-`). Zijn beide delen frequent, dan is het een doorzichtige samenstelling en telt het **niet** als moeilijk. `ziekenhuisopname` → `ziekenhuis` + `opname`, beide alledaags.
- Uitvoer: percentage moeilijke woorden én de zeldzaamste lemma's per hoofdstuk, zodat de auteur ze kan zien in plaats van alleen een getal.
- TTR en MTLD op spaCy-**lemma's** (niet op woordvormen — Nederlands verbuigt te veel), stopwoorden uit spaCy's `nl`-lijst. MTLD meteen bidirectioneel implementeren; de root-versie in `read_stats.py:219` doet alleen de voorwaartse pas, wat afwijkt van het gepubliceerde algoritme (McCarthy & Jarvis).

---

## Stijl (`stijl.py`) — wat het is en op wiens gezag

Dit is de enige module die inhoudelijk **schrijfadvies** geeft, dus hier is de bronvraag het scherpst. De drie constructies die we meten zijn geen persoonlijke voorkeuren: het zijn de klassieke Nederlandse stijlkwesties zoals beschreven door het **Genootschap Onze Taal** (Taalloket, thema *duidelijk schrijven*) en **Taaladvies.net**, de gezamenlijke adviesdienst van de **Nederlandse Taalunie** — de officiële instantie voor het Nederlands in Nederland, Vlaanderen en Suriname.

Het gereedschap is **spaCy `nl_core_news_sm`**: een model getraind op **UD Dutch Alpino** en **LassySmall** voor POS-tags en dependencies (NER uit LassySmall, OntoNotes-schema, door NLP Town), gelicentieerd **CC BY-SA 4.0**. Alpino en Lassy zijn de standaard Nederlandse syntactische treebanks (Alpino uit Groningen; Lassy uit het STEVIN-programma) — met andere woorden: de grammaticale analyse leunt op de geannoteerde corpora die het Nederlandse taaltechnologieveld zelf als referentie gebruikt. Omdat het om **Universal Dependencies** gaat, zijn labels als `aux:pass` en `nsubj:pass` beschikbaar; dat is wat passiefdetectie zonder regex mogelijk maakt.

- **Lijdende vorm**: `aux:pass` / `nsubj:pass`-dependencies, met `worden`/`zijn` + voltooid deelwoord als terugval. Percentage zinnen plus de zinnen zelf. *Onze Taal ontraadt de lijdende vorm niet categorisch* — hij is functioneel als de handelende persoon er niet toe doet — dus rapporteren we een **aandeel met voorbeelden**, geen foutmelding.
- **Naamwoordstijl**: het vervangen van een werkwoord door een naamwoord plus hulpwerkwoord ("een beslissing nemen" i.p.v. "beslissen"). Onze Taal beschrijft het effect als *afstandelijker, en daardoor de boodschap verzachtend* — in fictie soms precies de bedoeling, dus opnieuw: signaleren, niet veroordelen. Detectie: `NOUN`-lemma's op `-ing, -atie, -tie, -heid, -iteit, -isme, -ering, -sel` in combinatie met een licht werkwoord (`doen, maken, geven, plaatsvinden, hebben`).
- **Tangconstructie**: Onze Taal en Taaladvies.net definiëren dit als een **te grote afstand tussen bij elkaar horende zinsdelen**, en noemen daarbij drie specifieke gevallen: tussen de delen van een **scheidbaar werkwoord**, tussen **hulpwerkwoord en hoofdwerkwoord**, en tussen **lidwoord en zelfstandig naamwoord**. Dat sturen we rechtstreeks de implementatie in: we meten de tokenafstand voor precies díé drie relaties (via `compound:prt`, `aux`/`aux:pass` en `det`), in plaats van vaag "lange afstanden" te tellen. Zinnen boven de drempel (standaard 8 tokens, instelbaar) worden met context gemeld.
- **Schrapwoorden**: verzorgde lijst in `teksten.py` (`eigenlijk, gewoon, echt, natuurlijk, best wel, even, toch, nogal, tamelijk, simpelweg, in feite, als het ware, blijkbaar, kennelijk, wellicht, ergens, heel erg, zeer, ontzettend, absoluut, alsmaar, steeds maar`). Dit is de enige lijst zonder één gezaghebbende bron — het is redactionele conventie, geen taalregel. Dat staat er in het rapport ook bij, en de lijst is bewust op één plek aanpasbaar zodat de auteur hem naar eigen hand kan zetten.

**Verificatiestap vóór we hierop bouwen:** dump de daadwerkelijke dependency-labels van `nl_core_news_sm` op een handvol bekende passief- en tangzinnen en bevestig dat `aux:pass`/`nsubj:pass`/`compound:prt` in dit model écht voorkomen. Het labelinventaris is modelspecifiek; erop vertrouwen zonder te kijken is precies hoe zo'n module stil kapot gaat.

---

## Dialoog en tempo (`dialoog.py`) — wat het is en op wiens gezag

Voor dialoogopmaak in het Nederlands bestaat **geen officiële regel**, en dat is zelf de belangrijkste bevinding uit de bronnen. Onze Taal en de Nederlandse redactiepraktijk zijn eenduidig: enkele of dubbele aanhalingstekens is **een kwestie van smaak**, waarbij enkele (`'…'`) tegenwoordig de voorkeur hebben omdat ze een rustiger tekstbeeld geven, terwijl vroeger dubbele gebruikelijker waren. Wat wél als regel geldt:

- **consequent zijn** binnen één tekst;
- bij een citaat **binnen** een citaat schakel je naar de andere soort;
- wordt een volledige zin geciteerd, dan staan punt, vraagteken en uitroepteken **binnen** de aanhalingstekens.

Daaruit volgt een beter ontwerp dan "detecteer aanhalingstekens": de tool **detecteert eerst welke conventie dit manuscript hanteert** (`'…'`, `"…"`, `„…”`, `«…»`, of streepjesdialoog met `—`/`–` aan het regelbegin) en rapporteert daarna een **consistentiecontrole** — welke hoofdstukken van de dominante conventie afwijken. Voor een manuscript dat naar een uitgever gaat is dat concreter bruikbaar dan welke leesbaarheidsscore ook, en het is direct op de bovenstaande regel terug te voeren.

Verder per hoofdstuk:

- **Dialoogaandeel** (% woorden in dialoog), gemiddelde dialoogregellengte, verhouding dialoog/vertelling. Detectie op alinea-niveau, want dialoog is in Nederlands proza een alinea-eenheid.
- **Tempo**: zinslengtereeks per hoofdstuk → gemiddelde, mediaan, p90 en **spreiding**. Lage spreiding = monotoon ritme. Dit is descriptieve statistiek, geen geijkte index, en wordt als zodanig gepresenteerd: geen drempelwaarde, alleen het verloop over de hoofdstukken.

---

## Tekstinvoer (`tekst.py`)

- Normaliseer typografie vóór tokenisatie: `’ ‘ ‛` → `'`, maar `„ “ ” « »` **behouden** voor `dialoog.py` (die heeft ze nodig om de conventie te bepalen), `…` → `...`. Dit lost meteen de tokensplitsingsfout uit de Engelse versie op.
- **Hoofdstukdetectie binnen bestanden**: `^#{1,3}\s*(Hoofdstuk|Deel|Proloog|Epiloog|Voorwoord|Naschrift)\b` en kale `Hoofdstuk <getal|Romeins|woord>`. Alleen splitsen bij ≥2 treffers; anders blijft "één bestand = één hoofdstuk", zoals nu.
- **docx** beter dan de root-versie (`read_stats.py:124`, die alleen `doc.paragraphs` pakt): ook tabelcellen, en koppen herkennen via stijlnaam — een Nederlandse Word-installatie noemt die **`Kop 1`/`Kop 2`**, niet `Heading 1`. Beide accepteren.
- Mappen met een pad-component `draft` of `klad` overslaan.

## Zinssegmentatie (`taal.py`)

spaCy's sentencizer struikelt over Nederlandse afkortingen. Voeg tokenizer-excepties toe: `bijv. blz. bv. ca. d.w.z. e.d. e.a. enz. etc. evt. excl. incl. i.p.v. i.v.m. jl. m.a.w. m.b.t. m.n. nl. n.a.v. o.a. o.b.v. o.i.d. resp. t.o.v. t.b.v. v.Chr. n.Chr. dhr. mevr. mw. dr. drs. ir. ing. prof. mr.` plus rangtelwoorden (`1e`, `2e`, `3e`). Eén gedeelde `nlp`-instantie voor het hele proces; `nlp.pipe()` met batches over de hoofdstukken.

## Rapport (`rapport.py`)

Markdown + PDF, volledig Nederlands. Structuur van `08_report.py` als patroon (module-level `SECTIES`/`BEGRIPPEN`-data zodat md en PDF niet uiteenlopen, `Table`/`TableStyle`, zebra-rijen, `KeepTogether`), maar met eigen inhoud.

**Belangrijk PDF-detail:** registreer een Unicode-TTF met `pdfmetrics.registerFont(TTFont("DejaVuSans", ...))`. De huidige code omzeilt dit door kopteksten bewust ASCII te houden (`08_report.py:151`) — reportlab's ingebouwde Helvetica laat niet-WinAnsi-tekens stilzwijgend vallen, wat `„ ” –` en accenten uit de PDF sloopt. DejaVuSans zit al in de boom via matplotlib (`mpl-data/fonts/ttf/DejaVuSans.ttf`), dus geen extra download.

Secties: Samenvatting · Leesbaarheid per hoofdstuk · Zwaarste hoofdstukken · Woordenschat en moeilijke woorden · Stijl (schrapwoorden, passief, naamwoordstijl, tangconstructies) · Dialoog, consistentie en tempo · Verloop over het verhaal · Begrippenlijst · **Verantwoording en bronnen** · Voorbehoud.

Elke metriek krijgt in de begrippenlijst een regel "waar komt dit vandaan", gevoed uit `teksten.py`, zodat een redacteur die het rapport onder ogen krijgt kan nagaan waar een getal op steunt.

Grafieken: leesbaarheidscurve over hoofdstukvolgorde (met gearceerde interpretatieband in plaats van de Engelse `axhline(60)`), dialoogaandeel per hoofdstuk, zinslengteverdeling.

Momentopnames zoals nu: `rapporten/JJJJ-MM-DD-UUMM/`, `samenvatting.json`, symlink `laatste`, en een `index.md` met verschillen tussen runs — patroon overnemen uit `new_snapshot_dir` / `update_latest` / `write_index` in `08_report.py`.

---

## Afhankelijkheden

Als optionele groep in `pyproject.toml`, zodat de Engelse kant licht blijft:

```toml
[project.optional-dependencies]
nl = [
  "spacy>=3.7,<4",
  "pyphen>=0.15",
  "wordfreq==3.1.1",      # bevroren dataset; versie pinnen voor reproduceerbare scores
  "nl_core_news_sm @ https://github.com/explosion/spacy-models/releases/download/nl_core_news_sm-3.8.0/nl_core_news_sm-3.8.0-py3-none-any.whl",
]
```

Het model als vastgepinde wheel-URL in plaats van `python -m spacy download`, want dat laatste werkt slecht samen met uv-beheerde omgevingen. Let op: de modelversie moet met de spaCy-minor meebewegen. `run_nl.sh` draait `uv sync --extra nl` en geeft een Nederlandse foutmelding als het model ontbreekt.

Licenties om in `nl/README.md` vast te leggen: pyphen en de LibreOffice-afbreekwoordenboeken (GPL 2.0+ / LGPL 2.1+ / MPL 1.1), `nl_core_news_sm` (CC BY-SA 4.0), wordfreq (MIT, data onder diverse bronlicenties). Alleen relevant bij distributie, maar dan wel meteen goed.

---

## Verificatie

1. `uv run pytest nl/tests` — gouden lettergreeptabel (tegen pyphen én de fallback) en de handberekende Flesch-Douma en Leesindex A. Dit eerst groen krijgen.
2. **Dependency-labels bevestigen**: klein script dat `nl_core_news_sm` over vijf bekende passief- en tangzinnen haalt en de labels dumpt. Pas daarna `stijl.py` afbouwen.
3. `./nl/run_nl.sh rapport nl/tests/fixtures` — de hele keten op het meegeleverde Nederlandse voorbeeldmanuscript, inclusief het `.docx`-bestand met `Kop 1`-stijlen.
4. `qlmanage -p rapporten/laatste/rapport.pdf` (of `pdftoppm`, beide al toegestaan in `.claude/settings.json`) — **visueel controleren dat `„ ” – é ë` daadwerkelijk in de PDF staan**; dat is de test op de TTF-registratie.
5. Draaien op een echt Nederlands manuscript en de zeldzaamste-woordenlijst, de schrapwoord-vindplaatsen en de gemelde tangconstructies steekproefsgewijs nalopen. **De Zipf-drempel van 3.0 hier ijken**: melden de gerapporteerde woorden ook echt iets, of is de drempel te scherp/te ruim?
6. Controleren dat de Engelse kant onaangeroerd werkt: `./run.sh 8 <map>`.

## Voorbehoud om in het rapport te zetten

- **De formules zijn oud en omstreden.** Douma (1960) en Brouwer (1963) zijn ruim zestig jaar oud en meten alleen oppervlaktekenmerken — woordlengte en zinslengte — niet samenhang, structuur of voorkennis. Die kritiek is in het Nederlandse taalbeheersingsonderzoek uitgebreid gedocumenteerd (o.a. Lentz & Jansen, *Hoe begrijpelijk is mijn tekst?*, Onze Taal 2008; Kraf & Pander Maat, *Leesbaarheidsonderzoek: oude problemen, nieuwe kansen*, Tijdschrift voor Taalbeheersing 2009). Ze worden nog steeds gebruikt bij gebrek aan even eenvoudige alternatieven.
- **Er bestaat een moderne opvolger.** **T-Scan** en de daarop gebouwde **LiNT**-leesbaarheidsformule (Pander Maat e.a., Tijdschrift voor Taalbeheersing 2023) zijn de huidige stand van zaken voor het Nederlands. Die vergen een zwaardere infrastructuur dan deze tool; als de behoefte groeit, is dat het pad — en het rapport zegt dat, in plaats van te suggereren dat Douma het laatste woord is.
- **Geijkt op zakelijke en educatieve tekst, niet op fictie.** Voor een roman zegt de **verschuiving tussen hoofdstukken** meer dan het absolute getal. Dat is ook waarom de tool consequent het verloop plot en niet één eindcijfer geeft.
- **`nl_core_news_sm` is het kleine model**; passief- en dependency-herkenning is goed maar niet foutloos. Modelnaam configureerbaar maken (env `RS_SPACY_MODEL`) zodat `nl_core_news_md` een upgrade van één regel is.
- **Fog-NL en de schrapwoordenlijst zijn van ons**, niet uit de literatuur — expliciet zo gelabeld.

## `nl/README.md` — de verantwoording, volledig uitgeschreven

Dit is een **kerndeliverable**, geen bijlage. De README moet een lezer die de tool niet kent — een redacteur, een medeauteur, of jijzelf over twee jaar — kunnen laten nagaan waar élk getal in het rapport op steunt, zónder de code te openen. Volledig in het Nederlands.

**Opzet:**

1. **Wat dit is** — één alinea: leesbaarheids- en stijlanalyse voor Nederlandse manuscripten, per hoofdstuk, zonder taalmodel. Expliciet: *elk cijfer is rekenwerk over de tekst, er komt geen AI aan te pas en er gaat geen tekst het internet op.*
2. **Snel starten** — `./nl/run_nl.sh`, het menu, de Finder-drag, en de losse subcommando's. Wat er waar terechtkomt (`rapporten/laatste/`).
3. **Wat de tool met je bestanden doet** — invoercontract: `.md` en `.docx`, recursief, `draft`/`klad` overgeslagen, hoofdstukdetectie, hoe volgorde wordt bepaald.
4. **De maten, één blok per maat.** Dit is het hart van de README. Voor Flesch-Douma, Leesindex A, Fog-NL, moeilijkheidspercentage, TTR/MTLD, lijdende vorm, naamwoordstijl, tangconstructie, schrapwoorden, dialoogaandeel, quote-consistentie en zinsritme telkens dezelfde vier kopjes:
   - **Wat het meet** — in gewone taal, één of twee zinnen.
   - **Waar het vandaan komt** — de bron, met auteur, jaartal, publicatie en link. Bij Douma en Brouwer de volledige formule uitgeschreven met de betekenis van elke variabele. Bij de stijlmaten: Onze Taal / Taaladvies.net, met de definitie in hun bewoordingen.
   - **Hoe wij het berekenen** — de concrete implementatiekeuzes: welke tokenizer, welke drempel, wat we uitsluiten. Hier hoort ook wat we *anders* doen dan de bron en waarom (Fog-NL's afwijkende definitie van "moeilijk woord"; de bidirectionele MTLD).
   - **Beperkingen** — waar de maat de mist in gaat. Eerlijk, niet defensief.
5. **Wat de tool níét meet** — plot, spanning, karaktertekening, samenhang, feitelijke juistheid. Voorkomt dat een laag cijfer als literair oordeel wordt gelezen.
6. **Waarom deze formules, en wat er beter is** — de eerlijke paragraaf: Douma en Brouwer zijn zestig jaar oud en bekritiseerd (Lentz & Jansen; Kraf & Pander Maat); T-Scan en LiNT zijn de moderne stand van zaken; wij gebruiken de klassiekers omdat ze eenvoudig, offline en per hoofdstuk vergelijkbaar zijn, en omdat het bij fictie tóch om het verloop gaat, niet om het absolute getal.
7. **Onderliggende bronnen en licenties** — pyphen + LibreOffice-afbreekwoordenboeken (GPL 2.0+ / LGPL 2.1+ / MPL 1.1), `nl_core_news_sm` op UD Alpino + LassySmall (CC BY-SA 4.0), wordfreq (MIT; dataset bevroren sinds september 2024, mét de reden). Wat dat betekent als deze repo ooit gedistribueerd wordt.
8. **Volledige literatuurlijst** — de lijst hieronder, met werkende links.
9. **Aanpassen** — waar je de schrapwoordenlijst, de Zipf-drempel en de tangconstructie-afstand bijstelt (`teksten.py`), en waarom je dat zou willen.

De begrippenlijst in het PDF-rapport en de blokken uit punt 4 komen **uit dezelfde data in `teksten.py`**, zodat README en rapport niet uiteen kunnen lopen — hetzelfde principe waarmee `08_report.py` nu al markdown en PDF synchroon houdt.

## Bronnen

Komen in `nl/README.md` (punt 8) en in de rapportsectie "Verantwoording".

- Douma, W.H. (1960). *De leesbaarheid van landbouwbladen*. Bulletin 17, Afd. Sociologie/Sociografie, Landbouwhogeschool Wageningen. — [overzicht Nederlandse formules, Kennisbank Begrijpelijke Taal](https://kennisbank-begrijpelijketaal.nl/begripsvoorspelling/ned_formules) · [Leesbaarheid, Wikipedia NL](https://nl.wikipedia.org/wiki/Leesbaarheid)
- Brouwer, R.H.M. (1963). Onderzoek naar de leesmoeilijkheid van Nederlands proza. *Pedagogische Studiën* 40. — [artikel-PDF](https://pedagogischestudien.nl/article/download/16764/18235/35177) · [AVI (onderwijs), Wikipedia NL](https://nl.wikipedia.org/wiki/AVI_(onderwijs))
- Lentz, L. & Jansen, C. (2008). Hoe begrijpelijk is mijn tekst? De opkomst, neergang en terugkeer van de leesbaarheidsformules. *Onze Taal* 77(1). — [PDF](https://www.researchgate.net/profile/Lr-Lentz/publication/46710334_Hoe_begrijpelijk_is_mijn_tekst_De_opkomst_neergang_en_terugkeer_van_de_leesbaarheidsformules/links/00b7d526a15fd4c09f000000/Hoe-begrijpelijk-is-mijn-tekst-De-opkomst-neergang-en-terugkeer-van-de-leesbaarheidsformules.pdf)
- Pander Maat, H. e.a. (2023). LiNT: een leesbaarheidsformule en een leesbaarheidsinstrument. *Tijdschrift voor Taalbeheersing*. — [AUP Online](https://www.aup-online.com/content/journals/10.5117/TVT2023.3.002.MAAT)
- De Clercq, O. & Hoste, V. (2014). *Hoe meetbaar is leesbaarheid?* — [LT3, UGent](https://lt3.ugent.be/media/uploads/publications/2014/liberamicorum_2014_DeClercq.pdf)
- Genootschap Onze Taal, Taalloket: [tangconstructie](https://onzetaal.nl/taalloket/tangconstructie) · [naamwoordstijl](https://onzetaal.nl/taalloket/naamwoordstijl) · [duidelijk schrijven](https://onzetaal.nl/taalloket/thematisch-taaladvies/duidelijk-schrijven) · [dubbele aanhalingstekens](https://onzetaal.nl/taalloket/aanhalingstekens-dubbele-aanhalingstekens)
- Taaladvies.net (Nederlandse Taalunie): [tangconstructie](https://taaladvies.net/taal/advies/term/84/tangconstructie/)
- Aanhalingstekens bij citeren, *Onze Taal* jrg. 69 — [DBNL](https://www.dbnl.org/tekst/_taa014200001_01/_taa014200001_01_0012.php)
- Pyphen — [pyphen.org](https://pyphen.org/) · Hunspell-afbreekbibliotheek: [github.com/hunspell/hyphen](https://github.com/hunspell/hyphen)
- van Heuven, W.J.B., Mandera, P., Keuleers, E. & Brysbaert, M. (2014). SUBTLEX-UK. *QJEP* 67(6), 1176–1190 (Zipf-schaal) — [uitleg Zipf-schaal](https://www.wellformedness.com/blog/zipf-scale/)
- wordfreq (Robyn Speer) — [repo](https://github.com/rspeer/wordfreq) · [SUNSET.md, waarom het bevroren is](https://github.com/rspeer/wordfreq/blob/master/SUNSET.md)
- spaCy `nl_core_news_sm`, getraind op UD Dutch Alpino + LassySmall, CC BY-SA 4.0 — [spacy-models releases](https://github.com/explosion/spacy-models/releases/tag/nl_core_news_sm-2.3.0)

## Volgorde van uitvoering

1. `lettergrepen.py` + tests (fundament)
2. `tekst.py`, `taal.py` (invoer en segmentatie)
3. `formules.py` + tests
4. `woordenschat.py` (inclusief samenstellingssplitsing)
5. dependency-labels bevestigen → `stijl.py`, `dialoog.py`
6. `teksten.py` compleet maken (strings, drempels, bronblokken), dan `analyse.py` en `rapport.py`
7. `analyseer.py`, `run_nl.sh`, **`nl/README.md`**, verwijzing vanuit de hoofd-`README.md`

Stap 1–3 leveren al een bruikbare tool op; 4–6 zijn additief.

De bronblokken uit `nl/README.md` punt 4 worden **niet aan het eind bijgeschreven**: elke module levert bij oplevering meteen zijn eigen blok aan in `teksten.py` (wat het meet / waar het vandaan komt / hoe wij het berekenen / beperkingen). Stap 7 is dan het samenstellen en redigeren van de README uit materiaal dat er al ligt — niet het achteraf reconstrueren van verantwoording, want dan is precies de bron kwijt die dit hele stuk wil vastleggen.

---

*Volgens `CLAUDE.md` hoort een kopie van dit plan bij aanvang van de uitvoering in `docs/plans/2026-08-31-nederlandse-leesbaarheid.md` te staan. Git-commando's worden niet door mij uitgevoerd; die lever ik als blok aan.*
