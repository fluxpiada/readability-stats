"""
woordenschat.py — hoe moeilijk zijn de woorden, en hoe gevarieerd.

**Moeilijkheid via frequentie, niet via lettergrepen.** Dit is de kern van wat
deze tool anders doet dan de Engelse variant. Gunning Fog noemt elk woord van
drie lettergrepen of meer "moeilijk"; in het Nederlands levert dat onzin op,
omdat samenstellingen aan elkaar worden geschreven. `ziekenhuisopname` is zes
lettergrepen en voor iedere lezer meteen duidelijk.

In plaats daarvan kijken we hoe vaak een woord in het Nederlands voorkomt, via
de **Zipf-schaal** (van Heuven, Mandera, Keuleers & Brysbaert, 2014): een
logaritmische maat waarop 1 ongeveer 0,01 voorkomen per miljoen woorden is en 7
ongeveer 100.000 per miljoen. De cijfers komen uit `wordfreq`, dat voor het
Nederlands onder meer Wikipedia, ondertitels, nieuws, boeken en webtekst
samenvoegt.

`wordfreq` wordt sinds september 2024 niet meer bijgewerkt: door generatieve AI
gegenereerde tekst had de webbronnen vervuild. Voor ons is dat geen bezwaar maar
een voordeel — de dataset ligt vast, dus scores blijven tussen runs
vergelijkbaar. De versie staat daarom gepind in pyproject.toml.

**Samenstellingscorrectie.** Een zeldzaam woord wordt alsnog niet als moeilijk
geteld als het uiteenvalt in delen die allemaal alledaags zijn. Dat is precies
het geval waar de lettergreepregel op stukloopt:

    ziekenhuisopname     zipf 2.71  ->  ziekenhuis (5.06) + opname (4.41)   gewoon
    vergunningsaanvraag  zipf 2.09  ->  vergunning (4.15) + aanvraag (4.35) gewoon
    melancholie          zipf 2.91  ->  valt nergens in uiteen              moeilijk
    obstinaat            zipf 1.32  ->  valt nergens in uiteen              moeilijk

De drempels staan hieronder als constanten en zijn bedoeld om aan te passen
(zie nl/README.md, "Aanpassen").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from .taal import woorden

# Onder deze Zipf-waarde heet een woord moeilijk: zeldzamer dan ongeveer
# één voorkomen per miljoen woorden.
ZIPF_DREMPEL = 3.0

# Een samenstelling telt als doorzichtig wanneer élk deel minstens zo frequent
# is. Strenger dan ZIPF_DREMPEL, zodat we niet elk zeldzaam woord wegredeneren
# via een toevallige klankopdeling.
ZIPF_DEEL_DREMPEL = 3.3

# Drie letters, want het Nederlands zit vol korte samenstellingsdelen:
# oog-arts, zee-man, koffie-zet-apparaat.
MINIMALE_DEELLENGTE = 3

# Achtervoegsels die als losse letterreeks frequent genoeg lijken, maar geen
# zelfstandig woord zijn. Zonder deze rem zou "stalling" uiteenvallen in
# "stal" + "ling" en daarmee ten onrechte als alledaags gelden. Een lengtegrens
# alleen vangt dit niet: "ling" en "zet" zijn even lang, maar "zet" is een woord.
NIET_ZELFSTANDIG = frozenset(
    {
        "ing", "ling", "heid", "lijk", "sel", "tie", "aat", "iek", "isme",
        "baar", "loos", "achtig", "erig", "ster", "teit", "erij", "nis",
        "schap", "dom", "ette", "eren", "end", "ende",
    }
)

# Nederlandse tussenklanken in samenstellingen: bloem-en-perk, vergunning-s-aanvraag.
TUSSENKLANKEN = ("s", "en", "e", "er", "n")

# Hoe diep we blijven splitsen: koffie|zet|apparaat is drie delen.
MAXIMALE_DIEPTE = 3


@dataclass
class Woordenschat:
    woorden: int
    moeilijke_woorden: int
    moeilijk_pct: float
    ttr: float
    mtld: float
    zeldzaamste: list[tuple[str, float]] = field(default_factory=list)
    samenstellingen_gered: int = 0


# ---------------------------------------------------------------
# Frequentie
# ---------------------------------------------------------------

@lru_cache(maxsize=200_000)
def zipf(woord: str) -> float:
    """Zipf-frequentie van *woord* in het Nederlands; 0.0 als het onbekend is."""
    from wordfreq import zipf_frequency

    return zipf_frequency(woord.lower(), "nl")


def _bruikbaar_deel(deel: str) -> bool:
    """Is dit stuk een zelfstandig, alledaags woord?"""
    return (
        len(deel) >= MINIMALE_DEELLENGTE
        and deel not in NIET_ZELFSTANDIG
        and zipf(deel) >= ZIPF_DEEL_DREMPEL
    )


@lru_cache(maxsize=100_000)
def splits_samenstelling(woord: str, diepte: int = MAXIMALE_DIEPTE) -> tuple[str, ...]:
    """
    Splits *woord* in doorzichtige delen, of geef het woord ongesplitst terug.

    Probeert elke splitspositie, met en zonder tussenklank, en eist dat alle
    delen zelfstandige, frequente woorden zijn. Geeft het langste geslaagde
    resultaat, zodat `koffiezetapparaat` in drie delen uiteenvalt en niet in twee.
    """
    woord = woord.lower()
    if diepte <= 1 or len(woord) < 2 * MINIMALE_DEELLENGTE:
        return (woord,)

    beste: tuple[str, ...] | None = None

    for snede in range(MINIMALE_DEELLENGTE, len(woord) - MINIMALE_DEELLENGTE + 1):
        links = woord[:snede]
        if not _bruikbaar_deel(links):
            continue

        for tussen in ("",) + TUSSENKLANKEN:
            if tussen and not woord[snede:].startswith(tussen):
                continue
            rechts = woord[snede + len(tussen) :]
            if len(rechts) < MINIMALE_DEELLENGTE:
                continue

            if _bruikbaar_deel(rechts):
                kandidaat: tuple[str, ...] = (links, rechts)
            else:
                verder = splits_samenstelling(rechts, diepte - 1)
                if len(verder) == 1:
                    continue
                kandidaat = (links,) + verder

            if beste is None or len(kandidaat) > len(beste):
                beste = kandidaat

    return beste or (woord,)


def is_moeilijk(woord: str, drempel: float = ZIPF_DREMPEL) -> bool:
    """
    Is dit een moeilijk woord?

    Zeldzaam én niet te herleiden tot alledaagse delen.
    """
    if zipf(woord) >= drempel:
        return False
    delen = splits_samenstelling(woord)
    return len(delen) == 1


# ---------------------------------------------------------------
# Lexicale variatie
# ---------------------------------------------------------------

def ttr(tokens: list[str]) -> float:
    """Type-token ratio: aandeel unieke woorden. Loopt terug bij langere tekst."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def _mtld_richting(tokens: list[str], drempel: float) -> float:
    factoren = 0.0
    segment: list[str] = []
    uniek: set[str] = set()

    for token in tokens:
        segment.append(token)
        uniek.add(token)
        if len(uniek) / len(segment) < drempel:
            factoren += 1
            segment, uniek = [], set()

    if segment:
        verhouding = len(uniek) / len(segment)
        # deelfactor: hoe ver dit restsegment op weg was naar de drempel
        if verhouding < 1.0:
            factoren += (1 - verhouding) / (1 - drempel)

    if not factoren:
        # Geen enkel segment zakte ooit onder de drempel: elk woord is uniek.
        # Dat is maximale variatie, en de gangbare afspraak is dan de tekstlengte
        # terug te geven — niet 0, want dat zou juist minimale variatie betekenen.
        return float(len(tokens))

    return len(tokens) / factoren


def mtld(tokens: list[str], drempel: float = 0.72) -> float:
    """
    Measure of Textual Lexical Diversity (McCarthy & Jarvis).

    In beide richtingen gemeten en gemiddeld, zoals het gepubliceerde algoritme
    voorschrijft. De Engelse versie in `read_stats.py` doet alleen de
    voorwaartse doorloop en wijkt daarmee af.
    """
    if not tokens:
        return 0.0
    heen = _mtld_richting(tokens, drempel)
    terug = _mtld_richting(list(reversed(tokens)), drempel)
    if not heen or not terug:
        return heen or terug
    return (heen + terug) / 2


# ---------------------------------------------------------------
# Analyse per hoofdstuk
# ---------------------------------------------------------------

def analyseer(doc, drempel: float = ZIPF_DREMPEL, top: int = 15,
              woordtokens=None) -> Woordenschat:
    """
    Woordenschatcijfers voor één ontleed hoofdstuk.

    Eigennamen en getallen tellen niet mee als moeilijk woord: een lezer
    struikelt niet over een personagenaam, en anders zou elk verzonnen
    plaatsnaampje het percentage opblazen.

    *woordtokens* mag meekomen als de aanroeper `taal.woorden(doc)` al heeft.
    """
    if woordtokens is None:
        woordtokens = woorden(doc)

    lemmas: list[str] = []
    moeilijk: dict[str, float] = {}
    aantal_moeilijk = 0
    gered = 0

    for token in woordtokens:
        lemma = token.lemma_.lower() or token.text.lower()
        lemmas.append(lemma)

        if token.pos_ == "PROPN":
            continue

        # De Nederlandse lemmatiseerder maakt er soms een niet-bestaand woord van
        # ("vermoeiende" -> "vermoeien", "verstuurd" -> "verstuuren"). Zo'n vorm
        # komt in geen enkele frequentielijst voor en zou het woord ten onrechte
        # zeldzaam maken. We nemen daarom de bekendste van de twee vormen.
        oppervlakte = token.text.lower()
        zipf_lemma, zipf_oppervlakte = zipf(lemma), zipf(oppervlakte)
        if zipf_lemma >= zipf_oppervlakte:
            vorm, score = lemma, zipf_lemma
        else:
            vorm, score = oppervlakte, zipf_oppervlakte

        if score >= drempel:
            continue

        if len(splits_samenstelling(vorm)) > 1:
            gered += 1
            continue

        aantal_moeilijk += 1
        moeilijk[vorm] = score

    aantal = len(lemmas)
    zeldzaamste = sorted(moeilijk.items(), key=lambda p: p[1])[:top]

    return Woordenschat(
        woorden=aantal,
        moeilijke_woorden=aantal_moeilijk,
        moeilijk_pct=(100 * aantal_moeilijk / aantal) if aantal else 0.0,
        ttr=ttr(lemmas),
        mtld=mtld(lemmas),
        zeldzaamste=zeldzaamste,
        samenstellingen_gered=gered,
    )
