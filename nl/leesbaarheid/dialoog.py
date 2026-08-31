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

from .taal import is_woord

# De conventies die in Nederlands proza voorkomen. Volgorde doet er niet toe;
# we tellen welke het manuscript zelf het meest gebruikt.
CONVENTIES = {
    "enkele aanhalingstekens": ("'", "'"),
    "dubbele aanhalingstekens": ("“", "”"),
    "rechte dubbele aanhalingstekens": ('"', '"'),
    "lage aanhalingstekens": ("„", "”"),
    "guillemets": ("«", "»"),
}

# Een dialoogstreepje aan het begin van een alinea. Dit is waarom `tekst.py`
# regelbeginstreepjes niet als opsommingsteken wegstript.
_STREEPJE = re.compile(r"^\s*[—–-]\s+\S")

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
    gemiddelde_dialoogregel: float
    conventie: str | None              # de conventie van dít hoofdstuk
    conventies_gevonden: dict[str, int] = field(default_factory=dict)
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


def dominante_conventie(tekst: str) -> str | None:
    """De conventie die dit manuscript het vaakst gebruikt, of None."""
    telling = tel_conventies(tekst)
    if not telling:
        return None
    return max(telling.items(), key=lambda p: p[1])[0]


def is_dialoogalinea(alinea: str, conventie: str | None = None) -> bool:
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
    if conventie and conventie in _OPENERS and _OPENERS[conventie].search(alinea):
        return True
    return any(patroon.search(alinea) for patroon in _OPENERS.values())


def _woorden_in(tekst: str) -> int:
    return len(re.findall(r"[^\W\d_]+", tekst, re.UNICODE))


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

    eigen_conventie = dominante_conventie(tekst)

    dialoogalineas = [a for a in alineas if is_dialoogalinea(a, eigen_conventie)]
    woorden_dialoog = sum(_woorden_in(a) for a in dialoogalineas)
    woorden_totaal = sum(_woorden_in(a) for a in alineas)

    return Dialoog(
        alineas=len(alineas),
        dialoogalineas=len(dialoogalineas),
        dialoog_pct=(100 * woorden_dialoog / woorden_totaal) if woorden_totaal else 0.0,
        gemiddelde_dialoogregel=(
            woorden_dialoog / len(dialoogalineas) if dialoogalineas else 0.0
        ),
        conventie=eigen_conventie,
        conventies_gevonden=tel_conventies(tekst),
        wijkt_af=bool(
            eigen_conventie
            and manuscript_conventie
            and eigen_conventie != manuscript_conventie
        ),
    )


# ---------------------------------------------------------------
# Tempo
# ---------------------------------------------------------------

def zinslengtes(doc) -> list[int]:
    """Aantal woorden per zin."""
    lengtes = []
    for zin in doc.sents:
        aantal = sum(1 for token in zin if is_woord(token))
        if aantal:
            lengtes.append(aantal)
    return lengtes


def analyseer_tempo(doc) -> Tempo:
    """
    Ritme van de zinslengte.

    De spreiding is hier de interessantste maat: een hoofdstuk waarin elke zin
    ongeveer even lang is, leest vlak, of die zinnen nu kort of lang zijn.
    """
    lengtes = zinslengtes(doc)
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
