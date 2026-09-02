"""
stijl.py — lijdende vorm, naamwoordstijl, tangconstructies en schrapwoorden.

Dit is de enige module die inhoudelijk schrijfadvies raakt, dus hier telt de
bronvraag het zwaarst. De drie constructies die we meten zijn geen persoonlijke
voorkeuren maar de klassieke Nederlandse stijlkwesties, zoals beschreven door
het **Genootschap Onze Taal** (Taalloket, thema *duidelijk schrijven*) en
**Taaladvies.net**, de adviesdienst van de **Nederlandse Taalunie**.

Belangrijk: het rapport **signaleert, het keurt niet af**. Onze Taal ontraadt de
lijdende vorm niet categorisch — hij is functioneel als de handelende persoon
er niet toe doet — en naamwoordstijl noemen ze afstandelijker, wat in fictie
juist het gewenste effect kan zijn. We geven daarom aandelen met voorbeelden,
zodat de auteur zelf kan oordelen, en nergens een foutmelding.

**Tangconstructie.** Onze Taal en Taaladvies.net omschrijven dit als een te
grote afstand tussen zinsdelen die bij elkaar horen, en noemen daarbij drie
gevallen: tussen de delen van een scheidbaar werkwoord, tussen hulpwerkwoord en
hoofdwerkwoord, en tussen lidwoord en zelfstandig naamwoord. Precies die drie
meten we, via de dependency-labels `compound:prt`, `aux`/`aux:pass` en `det` —
niet "lange afstanden" in het algemeen.

**Schrapwoorden** zijn de uitzondering: daarvoor bestaat geen gezaghebbende
lijst. Het is redactionele conventie, geen taalregel. De lijst staat daarom hier
als gewone constante en is bedoeld om aan te passen (zie nl/README.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .taal import is_woord, woorden as woordtokens, zinnen as zinlijst

# Afstand in tokens waarboven we van een tangconstructie spreken. Onze Taal
# noemt geen getal — "te groot" is een leesoordeel — dus dit is onze drempel.
TANG_DREMPEL = 8

# Achtervoegsels waarmee van een werkwoord een naamwoord wordt gemaakt.
NOMINALISATIE_ACHTERVOEGSELS = (
    "ing", "atie", "tie", "heid", "iteit", "isme", "ering", "sel", "ment",
)

# De hulpwerkwoorden waarmee zo'n naamwoord weer een handeling moet voorstellen:
# "een beslissing nemen" in plaats van "beslissen".
LICHTE_WERKWOORDEN = frozenset(
    {"doen", "maken", "geven", "nemen", "plaatsvinden", "hebben", "verrichten",
     "uitvoeren", "brengen", "houden"}
)

# Stopwoorden, stoplappen en versterkers. Geen taalregel maar redactiepraktijk:
# ze verzwakken meestal de zin die ze moeten versterken.
SCHRAPWOORDEN = frozenset(
    {
        "eigenlijk", "gewoon", "echt", "natuurlijk", "nogal", "tamelijk",
        "redelijk", "simpelweg", "blijkbaar", "kennelijk", "wellicht",
        "ergens", "zeer", "ontzettend", "absoluut", "alsmaar", "even",
        "eventjes", "toch", "best", "zeker", "feitelijk", "uiteraard",
        "gewoonweg", "weliswaar",
    }
)
# Let op: "min" hoort hier niet los in — dat is een gewoon woord ("min veertien
# graden"). Alleen de uitdrukking "min of meer" telt, en die staat hieronder.

# Uitdrukkingen van meerdere woorden; die vind je niet met een tokenlijst.
SCHRAPUITDRUKKINGEN = (
    "in feite", "als het ware", "een beetje", "heel erg", "min of meer",
    "zo'n beetje", "naar mijn mening", "het feit dat", "steeds maar",
    "op een gegeven moment", "in zekere zin",
)

_UITDRUKKINGEN = re.compile(
    r"\b(" + "|".join(re.escape(u) for u in SCHRAPUITDRUKKINGEN) + r")\b",
    re.I,
)


@dataclass
class Vindplaats:
    """Eén gevonden geval, met genoeg context om er iets mee te kunnen."""

    zin: str
    detail: str


@dataclass
class Stijl:
    zinnen: int
    woorden: int

    passief_zinnen: int
    passief_pct: float

    naamwoordstijl: int
    naamwoordstijl_per_1000: float

    tang_pct: float

    schrapwoorden: int
    schrapwoorden_per_1000: float

    voorbeelden: dict[str, list[Vindplaats]] = field(default_factory=dict)


def _kort(zin, maximaal: int = 160) -> str:
    tekst = " ".join(str(zin).split())
    return tekst if len(tekst) <= maximaal else tekst[: maximaal - 1] + "…"


# ---------------------------------------------------------------
# Losse detectoren, per zin
# ---------------------------------------------------------------

def is_passief(zin) -> bool:
    """
    Lijdende vorm: een hulpwerkwoord met de rol `aux:pass`.

    Dat label dekt zowel "werd ondertekend" als "is verkocht"; op het onderwerp
    afgaan werkt minder goed, omdat het model dat niet altijd als `nsubj:pass`
    markeert.
    """
    return any(token.dep_ == "aux:pass" for token in zin)


def heeft_agens(zin) -> bool:
    """
    Staat erbij wie het deed ("door de directeur")?

    Het label `obl:agent` alleen is niet genoeg: het kleine model kent dat niet
    consequent toe. "door de directeur" krijgt het wel, "door zijn zus" niet —
    daar wordt het een gewone `obl`. Daarom zoeken we ook structureel naar een
    bijwoordelijke bepaling met het voorzetsel "door" eraan vast.
    """
    for token in zin:
        if token.dep_ == "obl:agent":
            return True
        if token.dep_ == "obl" and any(
            kind.dep_ == "case" and kind.text.lower() == "door"
            for kind in token.children
        ):
            return True
    return False


# Alleen de relaties die Onze Taal en Taaladvies.net noemen tellen mee.
_TANGRELATIES = {
    "compound:prt": "scheidbaar werkwoord",
    "aux": "hulpwerkwoord en hoofdwerkwoord",
    "aux:pass": "hulpwerkwoord en hoofdwerkwoord",
    "det": "lidwoord en zelfstandig naamwoord",
}


def tangconstructie(zin) -> tuple[int, str] | None:
    """
    Grootste afstand tussen bij elkaar horende zinsdelen, als die te groot is.

    Geeft (afstand, omschrijving) terug, of None.
    """
    ergste: tuple[int, str] | None = None
    for token in zin:
        soort = _TANGRELATIES.get(token.dep_)
        if soort is None:
            continue
        afstand = abs(token.i - token.head.i)
        if afstand > TANG_DREMPEL and (ergste is None or afstand > ergste[0]):
            ergste = (afstand, soort)

    return ergste


def naamwoordstijl(zin) -> list[tuple[str, str]]:
    """
    Naamwoordstijl: een nominalisatie die aan een licht werkwoord hangt.

    "een beslissing nemen" telt; "de beslissing viel zwaar" niet — daar is het
    naamwoord gewoon het onderwerp en valt er niets te vereenvoudigen.
    """
    gevonden: list[tuple[str, str]] = []
    for token in zin:
        if token.pos_ != "NOUN":
            continue
        lemma = token.lemma_.lower()
        if not lemma.endswith(NOMINALISATIE_ACHTERVOEGSELS):
            continue
        hoofd = token.head
        if hoofd.pos_ in ("VERB", "AUX") and hoofd.lemma_.lower() in LICHTE_WERKWOORDEN:
            gevonden.append((lemma, hoofd.lemma_.lower()))
    return gevonden


def schrapwoorden_in(zin) -> list[str]:
    """Losse stopwoorden plus uitdrukkingen van meerdere woorden."""
    gevonden = [
        token.text.lower()
        for token in zin
        if is_woord(token) and token.text.lower() in SCHRAPWOORDEN
    ]
    gevonden += [t.group(1).lower() for t in _UITDRUKKINGEN.finditer(str(zin))]
    return gevonden


# ---------------------------------------------------------------
# Per hoofdstuk
# ---------------------------------------------------------------

def analyseer(doc, voorbeelden_per_soort: int = 8, zinnen=None, aantal_woorden=None) -> Stijl:
    """
    Alle stijlmaten voor één ontleed hoofdstuk.

    *zinnen* en *aantal_woorden* mogen meekomen als de aanroeper die al heeft:
    `is_woord` draait dan niet nog een keer over elk token van het hoofdstuk.
    """
    if zinnen is None:
        zinnen = zinlijst(doc)
    if aantal_woorden is None:
        aantal_woorden = len(woordtokens(doc))
    aantal_zinnen = len(zinnen)

    passief = tang = 0
    nominalisaties = 0
    telling: dict[str, int] = {}
    voorbeelden: dict[str, list[Vindplaats]] = {
        "passief": [],
        "naamwoordstijl": [],
        "tangconstructie": [],
        "schrapwoorden": [],
    }

    for zin in zinnen:
        if is_passief(zin):
            passief += 1
            # heeft_agens loopt de hele zin langs en is alleen nodig voor de
            # omschrijving bij een voorbeeld, niet voor een telling.
            if len(voorbeelden["passief"]) < voorbeelden_per_soort:
                agens = heeft_agens(zin)
                voorbeelden["passief"].append(
                    Vindplaats(
                        _kort(zin),
                        "met handelende persoon" if agens else "zonder handelende persoon",
                    )
                )

        gevonden_tang = tangconstructie(zin)
        if gevonden_tang:
            tang += 1
            afstand, soort = gevonden_tang
            if len(voorbeelden["tangconstructie"]) < voorbeelden_per_soort:
                voorbeelden["tangconstructie"].append(
                    Vindplaats(_kort(zin), f"{afstand} woorden tussen {soort}")
                )

        for lemma, werkwoord in naamwoordstijl(zin):
            nominalisaties += 1
            if len(voorbeelden["naamwoordstijl"]) < voorbeelden_per_soort:
                voorbeelden["naamwoordstijl"].append(
                    Vindplaats(_kort(zin), f"{lemma} + {werkwoord}")
                )

        woorden_hier = schrapwoorden_in(zin)
        for woord in woorden_hier:
            telling[woord] = telling.get(woord, 0) + 1
        if woorden_hier and len(voorbeelden["schrapwoorden"]) < voorbeelden_per_soort:
            voorbeelden["schrapwoorden"].append(
                Vindplaats(_kort(zin), ", ".join(sorted(set(woorden_hier))))
            )

    totaal_schrap = sum(telling.values())
    per_duizend = (lambda n: 1000 * n / aantal_woorden if aantal_woorden else 0.0)

    return Stijl(
        zinnen=aantal_zinnen,
        woorden=aantal_woorden,
        passief_zinnen=passief,
        passief_pct=(100 * passief / aantal_zinnen) if aantal_zinnen else 0.0,
        naamwoordstijl=nominalisaties,
        naamwoordstijl_per_1000=per_duizend(nominalisaties),
        tang_pct=(100 * tang / aantal_zinnen) if aantal_zinnen else 0.0,
        schrapwoorden=totaal_schrap,
        schrapwoorden_per_1000=per_duizend(totaal_schrap),
        voorbeelden=voorbeelden,
    )
