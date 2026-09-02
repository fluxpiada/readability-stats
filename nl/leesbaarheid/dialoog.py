"""
dialoog.py — dialoogaandeel, conventieconsistentie en zinsritme.

Voor dialoogopmaak in het Nederlands bestaat **geen officiële regel**, en dat is
zelf de belangrijkste bevinding. Onze Taal en de Nederlandse redactiepraktijk
zijn eenduidig: enkele of dubbele aanhalingstekens is een kwestie van smaak,
waarbij enkele (`'…'`) tegenwoordig de voorkeur hebben omdat ze een rustiger
tekstbeeld geven. Wat wél als regel geldt:

* wees **consequent** binnen één tekst;
* bij een citaat binnen een citaat schakel je naar de andere soort;
* citeer je een hele zin, dan staan punt, vraag- en uitroepteken binnen de
  aanhalingstekens.

Daarom detecteert deze module eerst welke conventie het manuscript zelf
hanteert, en rapporteert daarna welke hoofdstukken daarvan afwijken. Voor een
manuscript dat naar een uitgever gaat is die consistentiecontrole concreter
bruikbaar dan welk leesbaarheidscijfer ook.

Het tempo-deel is beschrijvende statistiek, geen geijkte index: gemiddelde,
mediaan, p90 en spreiding van de zinslengte. De spreiding is voor een roman het
interessantst — weinig variatie leest eentonig, ongeacht of de zinnen kort of
lang zijn.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from .lettergrepen import _LETTERS
from .taal import is_woord, zinnen

# Een dialoogstreepje aan het begin van een alinea. Dit is waarom `tekst.py`
# regelbeginstreepjes niet als opsommingsteken wegstript.
_STREEPJE = re.compile(r"^\s*[—–-]\s+\S")

# De conventies die in Nederlands proza voorkomen. Volgorde doet er niet toe;
# we tellen welke het manuscript zelf het meest gebruikt.
_OPENERS = {
    "enkele aanhalingstekens": re.compile(r"(?<![\w])'(?=\w)"),
    "dubbele aanhalingstekens": re.compile(r"“"),
    "rechte dubbele aanhalingstekens": re.compile(r'"(?=\w)'),
    "lage aanhalingstekens": re.compile(r"„"),
    "guillemets": re.compile(r"«"),
}


@dataclass
class Dialoog:
    alineas: int
    dialoogalineas: int
    dialoog_pct: float                 # aandeel woorden in dialoog
    conventie: str | None              # de conventie van dít hoofdstuk
    telling: dict[str, int] = field(default_factory=dict)   # per conventie, hoe vaak
    wijkt_af: bool = False             # ten opzichte van de rest van het manuscript


@dataclass
class Tempo:
    zinnen: int
    gemiddelde: float
    mediaan: float
    p90: float
    spreiding: float
    lengtes: list[int] = field(default_factory=list)


# ---------------------------------------------------------------
# Dialoog
# ---------------------------------------------------------------

def tel_conventies(tekst: str) -> dict[str, int]:
    """Hoe vaak komt elke openingsconventie voor?"""
    telling = {naam: len(patroon.findall(tekst)) for naam, patroon in _OPENERS.items()}
    telling["dialoogstreepje"] = sum(
        1 for regel in tekst.splitlines() if _STREEPJE.match(regel)
    )
    return {naam: n for naam, n in telling.items() if n}


def sterkste_conventie(telling: dict[str, int]) -> str | None:
    """De conventie die het vaakst voorkomt in *telling*, of None."""
    if not telling:
        return None
    return max(telling.items(), key=lambda p: p[1])[0]


def dominante_conventie(tekst: str) -> str | None:
    """De conventie die deze tekst het vaakst gebruikt, of None."""
    return sterkste_conventie(tel_conventies(tekst))


def is_dialoogalinea(alinea: str) -> bool:
    """
    Is deze alinea dialoog?

    Alinea-niveau, want in Nederlands proza is dialoog een alinea-eenheid: elke
    spreker krijgt een eigen alinea.

    Er wordt bewust op *alle* conventies gekeken, ook wanneer bekend is welke
    het manuscript meestal gebruikt. Anders telt juist het hoofdstuk dat afwijkt
    als "geen dialoog", en dat is precies het hoofdstuk dat we willen vinden.
    """
    if _STREEPJE.match(alinea):
        return True
    return any(patroon.search(alinea) for patroon in _OPENERS.values())


def _woorden_in(tekst: str) -> int:
    # Op onbewerkte tekst, dus zonder spaCy: dezelfde letterdefinitie als
    # `lettergrepen`, zodat de twee niet uit elkaar lopen.
    return sum(1 for _ in _LETTERS.finditer(tekst))


def analyseer_dialoog(tekst: str, manuscript_conventie: str | None = None) -> Dialoog:
    """
    Dialoogcijfers voor één hoofdstuk.

    *manuscript_conventie* is wat de rest van het boek doet; die wordt alleen
    gebruikt om te bepalen of dit hoofdstuk afwijkt. De conventie die we
    rapporteren is altijd die van het hoofdstuk zelf — anders zou elk hoofdstuk
    per definitie met het manuscript overeenkomen en vindt de controle nooit iets.
    """
    alineas = [a for a in re.split(r"\n\s*\n", tekst) if a.strip()]
    if not alineas:
        alineas = [tekst] if tekst.strip() else []

    telling = tel_conventies(tekst)
    eigen_conventie = sterkste_conventie(telling)

    # Eén doorloop over de alinea's: de dialoogalinea's zijn een deelverzameling
    # van alle alinea's, dus apart optellen zou ze een tweede keer tellen.
    aantal_dialoog = 0
    woorden_dialoog = 0
    woorden_totaal = 0
    for alinea in alineas:
        woorden = _woorden_in(alinea)
        woorden_totaal += woorden
        if is_dialoogalinea(alinea):
            aantal_dialoog += 1
            woorden_dialoog += woorden

    return Dialoog(
        alineas=len(alineas),
        dialoogalineas=aantal_dialoog,
        dialoog_pct=(100 * woorden_dialoog / woorden_totaal) if woorden_totaal else 0.0,
        conventie=eigen_conventie,
        telling=telling,
        wijkt_af=bool(
            eigen_conventie
            and manuscript_conventie
            and eigen_conventie != manuscript_conventie
        ),
    )


# ---------------------------------------------------------------
# Tempo
# ---------------------------------------------------------------

def zinslengtes(doc, zinlijst=None) -> list[int]:
    """Aantal woorden per zin, via dezelfde zin- en woorddefinitie als de rest."""
    return [sum(1 for token in zin if is_woord(token))
            for zin in (zinnen(doc) if zinlijst is None else zinlijst)]


def analyseer_tempo(doc, zinlijst=None) -> Tempo:
    """
    Ritme van de zinslengte.

    De spreiding is hier de interessantste maat: een hoofdstuk waarin elke zin
    ongeveer even lang is, leest vlak, of die zinnen nu kort of lang zijn.

    *zinlijst* mag meekomen als de aanroeper `taal.zinnen(doc)` al heeft: dat
    scheelt een doorloop over alle tokens.
    """
    lengtes = zinslengtes(doc, zinlijst)
    if not lengtes:
        return Tempo(0, 0.0, 0.0, 0.0, 0.0, [])

    gesorteerd = sorted(lengtes)
    index = max(0, min(len(gesorteerd) - 1, round(0.9 * (len(gesorteerd) - 1))))

    return Tempo(
        zinnen=len(lengtes),
        gemiddelde=statistics.fmean(lengtes),
        mediaan=statistics.median(lengtes),
        p90=float(gesorteerd[index]),
        spreiding=statistics.pstdev(lengtes) if len(lengtes) > 1 else 0.0,
        lengtes=lengtes,
    )
