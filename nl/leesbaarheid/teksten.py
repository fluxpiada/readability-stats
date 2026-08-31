"""
teksten.py — alle Nederlandse tekst van de tool op één plek.

Hier staan de namen van de maten, de verantwoording per maat, de
begrippenlijst, het voorbehoud en de literatuurlijst. Het rapport én
nl/README.md putten hieruit, zodat ze niet uiteen kunnen lopen — hetzelfde
principe waarmee `08_report.py` markdown en PDF synchroon houdt.

Wil je de toon van het rapport bijstellen, of de schrapwoordenlijst naar je hand
zetten, dan is dit het bestand. De drempelwaarden zelf staan bij de modules
waar ze horen (`woordenschat.ZIPF_DREMPEL`, `stijl.TANG_DREMPEL`).
"""

from __future__ import annotations

from dataclasses import dataclass

TITEL = "Leesbaarheidsrapport"
ONDERTITEL = "Nederlandse manuscriptanalyse per hoofdstuk"


@dataclass(frozen=True)
class Maat:
    """Eén maat, met de verantwoording die er in het rapport bij hoort."""

    sleutel: str
    naam: str
    wat: str
    bron: str
    hoe: str
    beperking: str


MATEN: tuple[Maat, ...] = (
    Maat(
        sleutel="flesch_douma",
        naam="Flesch-Douma",
        wat=(
            "Leesgemak op een schaal van ongeveer 0 (zeer moeilijk) tot 100 "
            "(zeer makkelijk), gebaseerd op woordlengte en zinslengte."
        ),
        bron=(
            "W.H. Douma (1960), 'De leesbaarheid van landbouwbladen', Bulletin 17, "
            "Landbouwhogeschool Wageningen. Douma herijkte de Reading Ease-formule "
            "van Rudolf Flesch op Nederlands materiaal; het is sindsdien de meest "
            "gebruikte Nederlandse leesbaarheidsmaat.\n"
            "Formule: 206,84 − 0,77 × (lettergrepen per 100 woorden) "
            "− 0,93 × (woorden per zin)."
        ),
        hoe=(
            "Zinnen en woorden komen uit de spaCy-pijplijn voor het Nederlands, "
            "met een lijst Nederlandse afkortingen zodat 'bijv.' geen zinseinde is. "
            "Lettergrepen worden geteld met de afbreekwoordenlijst nl_NL, aangevuld "
            "met een klinkerkernenteller."
        ),
        beperking=(
            "Meet alleen oppervlaktekenmerken: woord- en zinslengte, geen samenhang "
            "of voorkennis. Geijkt op zakelijke tekst, niet op fictie."
        ),
    ),
    Maat(
        sleutel="leesindex_a",
        naam="Leesindex A",
        wat="Tweede leesgemakmaat, onafhankelijk geijkt. Hoger is makkelijker.",
        bron=(
            "R.H.M. Brouwer (1963), 'Onderzoek naar de leesmoeilijkheid van "
            "Nederlands proza', Pedagogische Studiën 40. Jarenlang gebruikt als "
            "basis voor het bepalen van AVI-niveaus in het basisonderwijs.\n"
            "Formule: 195 − 67 × (lettergrepen per woord) − 2 × (woorden per zin)."
        ),
        hoe=(
            "Zelfde tellingen als Flesch-Douma. We rapporteren beide maten naast "
            "elkaar omdat ze op verschillend materiaal zijn geijkt: landbouwbladen "
            "tegenover proza."
        ),
        beperking=(
            "Zelfde bezwaar als Flesch-Douma. Lopen de twee maten voor een hoofdstuk "
            "uiteen, dan bewegen woordlengte en zinslengte tegen elkaar in — dat is "
            "zelf het signaal."
        ),
    ),
    Maat(
        sleutel="fog_nl",
        naam="Fog-NL",
        wat=(
            "Hoe zwaar de tekst is qua zinslengte en moeilijke woorden samen. "
            "Lager is toegankelijker."
        ),
        bron=(
            "GEEN GEPUBLICEERDE MAAT — dit is een bewerking van ons. De vorm komt "
            "van Gunning Fog, maar de definitie van 'moeilijk woord' is vervangen."
        ),
        hoe=(
            "0,4 × ((woorden per zin) + 100 × moeilijkwoordpercentage). Gunning Fog "
            "rekent elk woord van drie lettergrepen of meer als moeilijk; voor het "
            "Nederlands is dat onbruikbaar, omdat samenstellingen aan elkaar worden "
            "geschreven. Wij gebruiken het frequentiepercentage hieronder."
        ),
        beperking=(
            "Niet vergelijkbaar met gepubliceerde Fog-scores. Gebruik het om "
            "hoofdstukken onderling te vergelijken, niet als absoluut cijfer."
        ),
    ),
    Maat(
        sleutel="moeilijk_pct",
        naam="Moeilijke woorden",
        wat="Percentage woorden dat in het Nederlands zelden voorkomt.",
        bron=(
            "Zipf-schaal van van Heuven, Mandera, Keuleers & Brysbaert (2014), "
            "ingevoerd bij SUBTLEX-UK: een logaritmische frequentiemaat waarop 1 "
            "ongeveer 0,01 voorkomen per miljoen woorden is en 7 ongeveer 100.000. "
            "Cijfers uit de bibliotheek wordfreq, die voor het Nederlands onder meer "
            "Wikipedia, ondertitels, nieuws, boeken en webtekst samenvoegt."
        ),
        hoe=(
            "Een woord heet moeilijk onder Zipf 3,0. Eigennamen en getallen tellen "
            "niet mee: over een personagenaam struikelt niemand. Samenstellingen die "
            "uiteenvallen in alledaagse delen tellen evenmin mee — "
            "'ziekenhuisopname' is lang, niet moeilijk."
        ),
        beperking=(
            "De frequentielijst is bevroren sinds september 2024, omdat door AI "
            "gegenereerde tekst de webbronnen vervuilde. Dat maakt de cijfers juist "
            "reproduceerbaar, maar recent taalgebruik ontbreekt. De "
            "samenstellingssplitsing is een heuristiek en zit er soms naast."
        ),
    ),
    Maat(
        sleutel="mtld",
        naam="Woordvariatie (MTLD en TTR)",
        wat="Hoe gevarieerd de woordkeus is. Hoger is gevarieerder.",
        bron=(
            "MTLD: McCarthy & Jarvis, Measure of Textual Lexical Diversity. TTR is "
            "de eenvoudige verhouding tussen unieke woorden en het totaal."
        ),
        hoe=(
            "Gemeten over lemma's, niet over woordvormen: het Nederlands verbuigt te "
            "veel om 'liep' en 'lopen' als twee woorden te tellen. MTLD wordt in "
            "beide richtingen berekend en gemiddeld, zoals het gepubliceerde "
            "algoritme voorschrijft."
        ),
        beperking=(
            "TTR daalt vanzelf naarmate een tekst langer wordt en is daarom tussen "
            "hoofdstukken van ongelijke lengte slecht vergelijkbaar; MTLD is daar "
            "juist voor bedoeld."
        ),
    ),
    Maat(
        sleutel="passief_pct",
        naam="Lijdende vorm",
        wat="Percentage zinnen in de lijdende vorm ('de brief werd ondertekend').",
        bron=(
            "Genootschap Onze Taal, Taalloket, thema 'duidelijk schrijven'. Onze Taal "
            "ontraadt de lijdende vorm NIET categorisch: hij is functioneel wanneer "
            "de handelende persoon er niet toe doet."
        ),
        hoe=(
            "Via het dependency-label aux:pass in het spaCy-model voor het "
            "Nederlands. We melden apart hoeveel van die zinnen geen handelende "
            "persoon noemen (geen 'door wie'), want dat is het geval waarin de "
            "lijdende vorm iets verbergt."
        ),
        beperking=(
            "Signalering, geen fout. In fictie is de lijdende vorm vaak een bewuste "
            "keuze. Het kleine taalmodel zit er soms naast bij ingewikkelde zinnen."
        ),
    ),
    Maat(
        sleutel="tang_pct",
        naam="Tangconstructies",
        wat=(
            "Percentage zinnen waarin woorden die bij elkaar horen ver uit elkaar "
            "staan, zodat de lezer het begin moet vasthouden tot het eind."
        ),
        bron=(
            "Genootschap Onze Taal en Taaladvies.net (Nederlandse Taalunie). Zij "
            "omschrijven een tangconstructie als een te grote afstand tussen bij "
            "elkaar horende zinsdelen, en noemen drie gevallen: tussen de delen van "
            "een scheidbaar werkwoord, tussen hulpwerkwoord en hoofdwerkwoord, en "
            "tussen lidwoord en zelfstandig naamwoord."
        ),
        hoe=(
            "Precies die drie relaties worden gemeten (compound:prt, aux, det), niet "
            "lange afstanden in het algemeen. De grens ligt op 8 woorden; Onze Taal "
            "noemt geen getal, dus die drempel is van ons en is aanpasbaar."
        ),
        beperking=(
            "Een lange tussenzin is niet altijd fout — soms is het ritme. De drempel "
            "is een keuze, geen norm."
        ),
    ),
    Maat(
        sleutel="naamwoordstijl",
        naam="Naamwoordstijl",
        wat=(
            "Een werkwoord vervangen door een naamwoord plus hulpwerkwoord: "
            "'een beslissing nemen' in plaats van 'beslissen'."
        ),
        bron=(
            "Genootschap Onze Taal, Taalloket. Zij beschrijven het effect als "
            "afstandelijker, waardoor de boodschap wordt verzacht."
        ),
        hoe=(
            "Zelfstandige naamwoorden op -ing, -atie, -heid, -iteit en dergelijke, "
            "maar alleen wanneer ze aan een licht werkwoord hangen (doen, maken, "
            "geven, nemen, plaatsvinden). 'De beslissing viel zwaar' telt dus niet."
        ),
        beperking=(
            "In fictie kan afstandelijkheid precies de bedoeling zijn, bijvoorbeeld "
            "in ambtelijke dialoog. Signalering, geen fout."
        ),
    ),
    Maat(
        sleutel="schrapwoorden",
        naam="Schrapwoorden",
        wat=(
            "Stoplappen en versterkers per duizend woorden: eigenlijk, gewoon, "
            "echt, natuurlijk, in feite."
        ),
        bron=(
            "GEEN GEZAGHEBBENDE BRON — dit is redactionele conventie, geen taalregel. "
            "De lijst is samengesteld uit gangbaar schrijfadvies."
        ),
        hoe=(
            "Losse woorden worden op tokenniveau geteld, uitdrukkingen van meerdere "
            "woorden met een patroon over de zin. De lijst staat in teksten.py en is "
            "bedoeld om aan te passen aan je eigen stem."
        ),
        beperking=(
            "Sterk smaakgebonden. In dialoog zijn stopwoorden vaak juist realistisch: "
            "zo praten mensen. Lees de vindplaatsen, niet alleen het getal."
        ),
    ),
    Maat(
        sleutel="dialoog_pct",
        naam="Dialoogaandeel",
        wat="Percentage woorden dat in dialoogalinea's staat.",
        bron=(
            "Voor dialoogopmaak bestaat geen officiële Nederlandse regel. Onze Taal: "
            "enkele of dubbele aanhalingstekens is een kwestie van smaak, mits je "
            "consequent bent. Enkele aanhalingstekens gelden tegenwoordig als rustiger."
        ),
        hoe=(
            "De tool stelt eerst vast welke conventie het manuscript zelf hanteert "
            "('…', \"…\", „…\", «…» of een dialoogstreepje) en meet daarna op "
            "alinea-niveau, want in Nederlands proza krijgt elke spreker een eigen "
            "alinea."
        ),
        beperking=(
            "Een verteller die veel citeert, telt mee als dialoog. Lange "
            "dialoogalinea's met veel tussenzinnen worden volledig als dialoog geteld."
        ),
    ),
    Maat(
        sleutel="conventie",
        naam="Consistentie van dialoogtekens",
        wat="Welke aanhalingsconventie overheerst, en welke hoofdstukken afwijken.",
        bron=(
            "Onze Taal: welke soort je ook kiest, voer die consequent door; bij een "
            "citaat binnen een citaat schakel je naar de andere soort."
        ),
        hoe=(
            "Per hoofdstuk wordt geteld welke openingstekens voorkomen. Het "
            "manuscriptbrede maximum geldt als de gekozen conventie; hoofdstukken "
            "met een andere dominante soort worden gemeld."
        ),
        beperking=(
            "Citaten binnen citaten gebruiken terecht de andere soort en kunnen als "
            "afwijking opduiken. Controleer de melding voor je iets verandert."
        ),
    ),
    Maat(
        sleutel="tempo",
        naam="Zinsritme",
        wat=(
            "Gemiddelde, mediaan, p90 en spreiding van de zinslengte. De spreiding "
            "zegt het meest: weinig variatie leest vlak."
        ),
        bron="Beschrijvende statistiek, geen geijkte index en geen norm.",
        hoe=(
            "Woorden per zin, geteld over de zinnen die het taalmodel vindt. Er is "
            "bewust geen drempelwaarde: alleen het verloop over de hoofdstukken."
        ),
        beperking=(
            "Er bestaat geen goede of foute zinslengte. Dit is materiaal om naar te "
            "kijken, geen cijfer om te halen."
        ),
    ),
)

MAAT_PER_SLEUTEL = {m.sleutel: m for m in MATEN}


# ---------------------------------------------------------------
# Rapportsecties
# ---------------------------------------------------------------

SECTIES = (
    (
        "per_hoofdstuk",
        "Leesbaarheid per hoofdstuk",
        "Flesch-Douma en Leesindex A per hoofdstuk, in verhaalvolgorde. Voor een "
        "roman is de verschuiving tussen hoofdstukken informatiever dan het "
        "absolute cijfer.",
    ),
    (
        "zwaarste",
        "Zwaarste hoofdstukken",
        "Gesorteerd van moeilijk naar makkelijk. Dat een hoofdstuk hier bovenaan "
        "staat is geen fout — een beladen hoofdstuk mag traag lezen.",
    ),
    (
        "woordenschat",
        "Woordenschat",
        "Het aandeel zeldzame woorden en de variatie in woordkeus. Samenstellingen "
        "die uiteenvallen in alledaagse delen tellen niet als moeilijk.",
    ),
    (
        "stijl",
        "Stijl",
        "Lijdende vorm, tangconstructies, naamwoordstijl en schrapwoorden. Alles "
        "hier is signalering: het zijn keuzes, geen fouten.",
    ),
    (
        "dialoog",
        "Dialoog en tempo",
        "Hoeveel dialoog een hoofdstuk bevat, of de aanhalingstekens consequent "
        "zijn, en hoe gevarieerd de zinslengte is.",
    ),
)

CAVEAT = (
    "Dit rapport is rekenwerk over de tekst. Er komt geen taalmodel aan te pas "
    "dat een oordeel velt, en er is geen tekst naar buiten gegaan: alles is op "
    "deze computer berekend. Wat hier niet in staat, is of het verhaal werkt — "
    "plot, spanning, personages en samenhang worden niet gemeten en kunnen niet "
    "uit deze cijfers worden afgeleid."
)

VOORBEHOUD = (
    (
        "De formules zijn oud en bekritiseerd",
        "Douma (1960) en Brouwer (1963) zijn ruim zestig jaar oud en meten alleen "
        "woordlengte en zinslengte — niet samenhang, structuur of voorkennis. Die "
        "kritiek is uitvoerig gedocumenteerd (Lentz & Jansen 2008; Kraf & Pander "
        "Maat 2009). Ze worden nog steeds gebruikt bij gebrek aan even eenvoudige "
        "alternatieven.",
    ),
    (
        "Er bestaat een moderne opvolger",
        "T-Scan en de daarop gebouwde LiNT-formule (Pander Maat e.a., 2023) zijn de "
        "huidige stand van zaken voor het Nederlands. Die vragen een zwaardere "
        "infrastructuur dan deze tool. Groeit de behoefte, dan is dat het pad.",
    ),
    (
        "Geijkt op zakelijke tekst, niet op fictie",
        "De interpretatiebanden komen uit onderzoek naar voorlichtings- en "
        "onderwijsmateriaal. Voor een roman zegt het verloop tussen hoofdstukken "
        "meer dan het absolute getal.",
    ),
    (
        "Fog-NL en de schrapwoordenlijst zijn van ons",
        "Beide zijn geen gepubliceerde maat. Ze staan erin omdat ze bruikbaar zijn, "
        "niet omdat ze gezag hebben.",
    ),
    (
        "Het taalmodel is het kleine model",
        "nl_core_news_sm herkent de lijdende vorm en zinsdelen goed maar niet "
        "foutloos. Met de omgevingsvariabele RS_SPACY_MODEL kun je een groter model "
        "kiezen.",
    ),
)

LITERATUUR = (
    (
        "Douma, W.H. (1960). De leesbaarheid van landbouwbladen. Bulletin 17, "
        "Landbouwhogeschool Wageningen.",
        "https://kennisbank-begrijpelijketaal.nl/begripsvoorspelling/ned_formules",
    ),
    (
        "Brouwer, R.H.M. (1963). Onderzoek naar de leesmoeilijkheid van Nederlands "
        "proza. Pedagogische Studiën 40.",
        "https://pedagogischestudien.nl/article/download/16764/18235/35177",
    ),
    (
        "Lentz, L. & Jansen, C. (2008). Hoe begrijpelijk is mijn tekst? De opkomst, "
        "neergang en terugkeer van de leesbaarheidsformules. Onze Taal 77(1).",
        "https://www.uu.nl/staff/LRLentz/Publications",
    ),
    (
        "Pander Maat, H. e.a. (2023). LiNT: een leesbaarheidsformule en een "
        "leesbaarheidsinstrument. Tijdschrift voor Taalbeheersing.",
        "https://www.aup-online.com/content/journals/10.5117/TVT2023.3.002.MAAT",
    ),
    (
        "De Clercq, O. & Hoste, V. (2014). Hoe meetbaar is leesbaarheid? UGent.",
        "https://lt3.ugent.be/media/uploads/publications/2014/liberamicorum_2014_DeClercq.pdf",
    ),
    (
        "Genootschap Onze Taal, Taalloket: tangconstructie.",
        "https://onzetaal.nl/taalloket/tangconstructie",
    ),
    (
        "Genootschap Onze Taal, Taalloket: naamwoordstijl.",
        "https://onzetaal.nl/taalloket/naamwoordstijl",
    ),
    (
        "Genootschap Onze Taal, Taalloket: duidelijk schrijven.",
        "https://onzetaal.nl/taalloket/thematisch-taaladvies/duidelijk-schrijven",
    ),
    (
        "Taaladvies.net (Nederlandse Taalunie): tangconstructie.",
        "https://taaladvies.net/taal/advies/term/84/tangconstructie/",
    ),
    (
        "van Heuven, W.J.B., Mandera, P., Keuleers, E. & Brysbaert, M. (2014). "
        "SUBTLEX-UK. Quarterly Journal of Experimental Psychology 67(6).",
        "https://www.wellformedness.com/blog/zipf-scale/",
    ),
    (
        "wordfreq (Robyn Speer) — en waarom de dataset bevroren is.",
        "https://github.com/rspeer/wordfreq/blob/master/SUNSET.md",
    ),
    (
        "Pyphen — afbreken met Hunspell-woordenboeken uit LibreOffice.",
        "https://pyphen.org/",
    ),
    (
        "spaCy nl_core_news_sm — getraind op UD Dutch Alpino en LassySmall.",
        "https://github.com/explosion/spacy-models",
    ),
)

LICENTIES = (
    ("pyphen en de afbreekwoordenboeken (LibreOffice)", "GPL 2.0+ / LGPL 2.1+ / MPL 1.1"),
    ("spaCy-model nl_core_news_sm (UD Alpino + LassySmall)", "CC BY-SA 4.0"),
    ("wordfreq", "MIT; brondata onder uiteenlopende licenties"),
)
