"""
formules.py — de leesbaarheidsformules.

Twee ervan zijn gepubliceerd en op Nederlands materiaal geijkt; de derde is
onze eigen bewerking en wordt overal als zodanig gelabeld.

**Flesch-Douma (Douma, 1960).** W.H. Douma, landbouwsocioloog aan de
Landbouwhogeschool Wageningen, herijkte de Reading Ease-formule van Rudolf
Flesch op Nederlands materiaal in *De leesbaarheid van landbouwbladen*
(Bulletin 17, Afd. Sociologie en Sociografie). Het is sindsdien de meest
gebruikte Nederlandse leesbaarheidsmaat.

    206.84 − 0.77 × (lettergrepen per 100 woorden) − 0.93 × (woorden per zin)

**Leesindex A (Brouwer, 1963).** R.H.M. Brouwer, "Onderzoek naar de
leesmoeilijkheid van Nederlands proza", *Pedagogische Studiën* 40. Onafhankelijk
geijkt, jarenlang gebruikt als basis voor het bepalen van AVI-niveaus in het
basisonderwijs.

    195 − 67 × (lettergrepen per woord) − 2 × (woorden per zin)

We rapporteren beide náást elkaar, omdat ze op verschillend materiaal zijn
geijkt (landbouwbladen tegenover proza). Lopen ze voor een hoofdstuk uiteen,
dan is dat zelf het signaal: meestal bewegen woordlengte en zinslengte dan
tegen elkaar in.

**Fog-NL.** Geen gepubliceerde maat maar een bewerking van ons. Gunning Fog
rekent woorden van drie lettergrepen of meer als "moeilijk", en dat is voor het
Nederlands onbruikbaar: `ziekenhuisopname` is een doorzichtige samenstelling,
geen moeilijk woord. Wij houden de vorm van Fog aan maar vullen het
moeilijk-woordpercentage met de frequentiemaat uit `woordenschat.py`. De
uitkomst is dus **niet** vergelijkbaar met gepubliceerde Fog-scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lettergrepen import tel_lettergrepen

# Douma (1960)
DOUMA_BASIS = 206.84
DOUMA_WOORDLENGTE = 0.77          # per lettergreep per 100 woorden
DOUMA_ZINSLENGTE = 0.93           # per woord per zin

# Brouwer (1963)
BROUWER_BASIS = 195.0
BROUWER_WOORDLENGTE = 67.0        # per lettergreep per woord
BROUWER_ZINSLENGTE = 2.0          # per woord per zin

# Gunning Fog, alleen de vorm
FOG_FACTOR = 0.4

LANG_WOORD_LETTERS = 9            # "> 9 letters", gangbare Nederlandse proxy
LANG_WOORD_LETTERGREPEN = 4


@dataclass
class Leesbaarheid:
    """De uitkomsten voor één stuk tekst."""

    woorden: int
    zinnen: int
    lettergrepen: int
    flesch_douma: float
    leesindex_a: float
    fog_nl: float | None
    woorden_per_zin: float
    lettergrepen_per_woord: float
    lange_woorden_pct: float          # >= 4 lettergrepen
    lange_letters_pct: float          # > 9 letters
    moeilijke_woorden_pct: float | None = None
    _bron: dict = field(default_factory=dict, repr=False)


def flesch_douma(woorden: int, zinnen: int, lettergrepen: int) -> float:
    """Flesch-Douma (1960). Hoger = makkelijker; ruwweg 0 tot 100."""
    return (
        DOUMA_BASIS
        - DOUMA_WOORDLENGTE * (lettergrepen / woorden * 100)
        - DOUMA_ZINSLENGTE * (woorden / zinnen)
    )


def leesindex_a(woorden: int, zinnen: int, lettergrepen: int) -> float:
    """Leesindex A van Brouwer (1963). Hoger = makkelijker."""
    return (
        BROUWER_BASIS
        - BROUWER_WOORDLENGTE * (lettergrepen / woorden)
        - BROUWER_ZINSLENGTE * (woorden / zinnen)
    )


def fog_nl(woorden: int, zinnen: int, moeilijke_woorden: int) -> float:
    """
    Onze Fog-bewerking. Lager = toegankelijker.

    Let op: "moeilijk" is hier frequentiegebaseerd (zie `woordenschat.py`), niet
    "drie of meer lettergrepen". Niet vergelijkbaar met gepubliceerde Fog-scores.
    """
    return FOG_FACTOR * ((woorden / zinnen) + 100 * (moeilijke_woorden / woorden))


def bereken(
    woordteksten: list[str],
    aantal_zinnen: int,
    moeilijke_woorden: int | None = None,
) -> Leesbaarheid | None:
    """
    Reken alle maten uit voor een reeks woorden en een aantal zinnen.

    Geeft None terug bij lege tekst, zodat de aanroeper het hoofdstuk kan
    overslaan in plaats van een deling door nul te krijgen.
    """
    aantal_woorden = len(woordteksten)
    if aantal_woorden == 0 or aantal_zinnen == 0:
        return None

    per_woord = [tel_lettergrepen(w) for w in woordteksten]
    lettergrepen = sum(per_woord)

    lang_lettergrepen = sum(1 for n in per_woord if n >= LANG_WOORD_LETTERGREPEN)
    lang_letters = sum(1 for w in woordteksten if len(w) > LANG_WOORD_LETTERS)

    return Leesbaarheid(
        woorden=aantal_woorden,
        zinnen=aantal_zinnen,
        lettergrepen=lettergrepen,
        flesch_douma=flesch_douma(aantal_woorden, aantal_zinnen, lettergrepen),
        leesindex_a=leesindex_a(aantal_woorden, aantal_zinnen, lettergrepen),
        fog_nl=(
            fog_nl(aantal_woorden, aantal_zinnen, moeilijke_woorden)
            if moeilijke_woorden is not None
            else None
        ),
        woorden_per_zin=aantal_woorden / aantal_zinnen,
        lettergrepen_per_woord=lettergrepen / aantal_woorden,
        lange_woorden_pct=100 * lang_lettergrepen / aantal_woorden,
        lange_letters_pct=100 * lang_letters / aantal_woorden,
        moeilijke_woorden_pct=(
            100 * moeilijke_woorden / aantal_woorden
            if moeilijke_woorden is not None
            else None
        ),
    )


# ---------------------------------------------------------------
# Interpretatie
# ---------------------------------------------------------------
#
# De banden komen uit de gangbare Nederlandse presentatie van Flesch-Douma.
# Ze zijn geijkt op zakelijke en educatieve tekst, niet op fictie: voor een
# roman zegt de verschuiving tussen hoofdstukken meer dan het absolute cijfer.

BANDEN = (
    (90, "zeer makkelijk", "groep 7–8 basisschool"),
    (80, "makkelijk", "vmbo"),
    (70, "vrij makkelijk", "havo onderbouw"),
    (60, "standaard", "havo/vwo bovenbouw"),
    (50, "vrij moeilijk", "hbo"),
    (30, "moeilijk", "wo"),
    (0, "zeer moeilijk", "academisch, specialistisch"),
)


def band(score: float) -> tuple[str, str]:
    """(omschrijving, indicatie leesniveau) voor een Flesch-Douma-score."""
    for ondergrens, omschrijving, niveau in BANDEN:
        if score >= ondergrens:
            return omschrijving, niveau
    return BANDEN[-1][1], BANDEN[-1][2]
