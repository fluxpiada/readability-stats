"""
lettergrepen.py — lettergrepen tellen in Nederlandse woorden.

Dit is het fundament van de hele tool: Flesch-Douma, Leesindex A en het
percentage lange woorden erven allemaal rechtstreeks de fout van deze module.

De aanpak is hybride, omdat de twee voor de hand liggende methodes op
verschillende plekken misgaan:

1. **Pyphen** (Hunspell-afbreekpatronen uit de LibreOffice-woordenboeken,
   bestand `hyph_nl_NL`) kent de woordgrenzen van samenstellingen, maar volgt
   de Nederlandse *afbreekregels*. Die verbieden het afbreken van een losse
   letter, dus pyphen telt te laag waar een lettergreep uit één klinker
   bestaat:

       mooie   -> mooie      (1, moet 2)
       idee    -> idee       (1, moet 2)
       België  -> Bel-gië    (2, moet 3)

2. **Klinkerkernen tellen** lost precies die gevallen op, maar ziet niet dat
   een klinkerpaar over een lettergreepgrens kan lopen:

       museum  -> mu-seum    (2, moet 3; de "eu" is hier geen tweeklank)

Daarom: pyphen bepaalt de grenzen, en binnen elk fragment tellen we
klinkerkernen. De kernenteller hoeft dan alleen nog binnen korte fragmenten te
werken, wat een stuk eenvoudiger is dan over een heel woord.

Zonder pyphen valt de module terug op de kernenteller over het hele woord. Die
is goed maar niet gelijkwaardig; `tests/test_lettergrepen.py` legt vast waar de
twee mogen verschillen, zodat de terugval niet stilzwijgend afdrijft.

Let op: afbreekpunten zijn niet exact hetzelfde als fonologische lettergrepen —
de Nederlandse afbreekregels zijn deels morfologisch (`zieken-huis-op-na-me`).
Voor leesbaarheidsformules, die lettergrepen als *benadering* van
woordcomplexiteit gebruiken, is dat ruim voldoende. Het blijft een benadering.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

try:
    import pyphen
    _woordenboek = pyphen.Pyphen(lang="nl_NL")
    PYPHEN_BESCHIKBAAR = True
except Exception:          # pyphen ontbreekt, of geen nl_NL-woordenboek
    _woordenboek = None
    PYPHEN_BESCHIKBAAR = False


# ---------------------------------------------------------------
# Klinkerkernen
# ---------------------------------------------------------------
#
# Op lengte gesorteerd: de scanner probeert altijd eerst de langste kern, zodat
# "ooi" in "mooie" niet als "oo" + "i" uiteenvalt.

DRIELETTERKERNEN = ("aai", "ooi", "oei", "eeu", "ieu")

TWEELETTERKERNEN = (
    "aa", "ee", "oo", "uu",      # lange klinkers
    "ie", "oe", "eu", "ui",      # tweeklanken
    "ij", "ei", "ou", "au",      # tweeklanken
    "ai", "oi", "oo",            # leenwoorden en tussenwerpsels
)

KLINKERS = set("aeiouy")

# Een trema markeert in het Nederlands nu juist dát twee klinkers *niet* samen
# één klank vormen: "reünie", "zeeën", "coördinatie". De letter erna begint dus
# altijd een nieuwe kern. Dit is precies wat de Engelse teller in read_stats.py
# stukmaakt: die gooit de tekens weg in plaats van ze te lezen.
_TREMA = {"ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u", "ÿ": "y"}

# Accenten zonder trema (klemtoon, leenwoorden) horen juist wél bij de kern:
# "één" is één lettergreep, "café" telt gewoon als ca-fé.
_ACCENTEN = str.maketrans(
    {
        "á": "a", "à": "a", "â": "a", "ã": "a", "å": "a",
        "é": "e", "è": "e", "ê": "e",
        "í": "i", "ì": "i", "î": "i",
        "ó": "o", "ò": "o", "ô": "o", "õ": "o",
        "ú": "u", "ù": "u", "û": "u",
        "ý": "y",
        "ç": "c", "ñ": "n",
    }
)


def _ontleed(fragment: str) -> tuple[str, list[bool]]:
    """
    Zet een fragment om in (letters, trema-markering).

    Geeft de letters terug met accenten platgeslagen, plus per positie of daar
    een trema stond — die posities mogen nooit in een voorafgaande kern worden
    opgeslokt.
    """
    letters: list[str] = []
    trema: list[bool] = []

    for teken in unicodedata.normalize("NFC", fragment).lower():
        if teken in _TREMA:
            letters.append(_TREMA[teken])
            trema.append(True)
        else:
            letters.append(teken.translate(_ACCENTEN))
            trema.append(False)

    return "".join(letters), trema


def tel_kernen(fragment: str) -> int:
    """
    Tel de klinkerkernen in *fragment*.

    Scant van links naar rechts en pakt telkens de langste geldige kern
    (drie letters vóór twee vóór één). Een kern mag nooit over een trema heen
    lopen.
    """
    letters, trema = _ontleed(fragment)
    kernen = 0
    i = 0
    lengte = len(letters)

    while i < lengte:
        if letters[i] not in KLINKERS:
            i += 1
            continue

        for maat, geldige in ((3, DRIELETTERKERNEN), (2, TWEELETTERKERNEN)):
            if i + maat > lengte:
                continue
            # een trema binnen de kern (niet op de eerste letter) breekt hem op
            if any(trema[i + k] for k in range(1, maat)):
                continue
            if letters[i : i + maat] in geldige:
                kernen += 1
                i += maat
                break
        else:
            kernen += 1          # losse klinker
            i += 1

    return kernen


# ---------------------------------------------------------------
# Lettergrepen per woord
# ---------------------------------------------------------------

# Alles wat geen letter is verdwijnt, maar Unicode-letters blijven staan — het
# omgekeerde van `re.sub(r"[^a-z]", ...)`, dat accenten wist in plaats van vouwt.
_LETTERS = re.compile(r"[^\W\d_]+", re.UNICODE)


def _schoon(woord: str) -> str:
    """Houd alleen letters over; koppeltekens en apostrofs vallen weg."""
    return "".join(_LETTERS.findall(woord))


@lru_cache(maxsize=200_000)
def tel_lettergrepen(woord: str) -> int:
    """
    Aantal lettergrepen in *woord*, minimaal 1 voor een woord met letters.

    Gebruikt pyphen voor de lettergreepgrenzen en telt daarbinnen klinkerkernen.
    Zonder pyphen wordt over het hele woord geteld (zie de moduledocstring voor
    het verschil).
    """
    schoon = _schoon(woord)
    if not schoon:
        return 0

    if PYPHEN_BESCHIKBAAR:
        fragmenten = _woordenboek.inserted(schoon).split("-")
        totaal = sum(tel_kernen(f) for f in fragmenten if f)
    else:
        totaal = tel_kernen(schoon)

    return max(1, totaal)


def tel_lettergrepen_zonder_pyphen(woord: str) -> int:
    """
    Alleen de kernenteller, zonder woordenboek.

    Bestaat om in de tests naast `tel_lettergrepen` te kunnen worden gelegd, en
    is wat er draait als pyphen ontbreekt.
    """
    schoon = _schoon(woord)
    if not schoon:
        return 0
    return max(1, tel_kernen(schoon))


def tel_lettergrepen_reeks(woorden) -> int:
    """Som van de lettergrepen over een reeks woorden."""
    return sum(tel_lettergrepen(w) for w in woorden)
