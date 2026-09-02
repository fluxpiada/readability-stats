"""
analyse.py — alles samenbrengen tot één tabel per manuscript.

De volgorde is bewust: hoofdstukken worden in één spaCy-doorloop ontleed
(`nlp.pipe`), en pas daarna rekenen de losse modules erop door. Zo betaalt een
manuscript de ontleedkosten één keer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import dialoog as mod_dialoog
from . import formules, stijl, woordenschat
from .taal import huidig_model, verwerk, woorden as woordtokens, zinnen as zinlijst
from .tekst import Hoofdstuk, laad_hoofdstukken


@dataclass
class HoofdstukAnalyse:
    """Alle uitkomsten voor één hoofdstuk."""

    hoofdstuk: Hoofdstuk
    leesbaarheid: formules.Leesbaarheid
    woordenschat: woordenschat.Woordenschat
    stijl: stijl.Stijl
    dialoog: mod_dialoog.Dialoog
    tempo: mod_dialoog.Tempo


@dataclass
class Manuscript:
    """Het hele manuscript, plus wat er manuscriptbreed geldt."""

    map_pad: Path
    hoofdstukken: list[HoofdstukAnalyse] = field(default_factory=list)
    conventie: str | None = None
    # Welk taalmodel de cijfers heeft geproduceerd. De stijlpercentages
    # verschuiven als dit verandert, dus twee runs met verschillende modellen
    # zijn niet zonder meer vergelijkbaar. Daarom staat het in het rapport.
    taalmodel: str | None = None

    @property
    def woorden(self) -> int:
        return sum(h.leesbaarheid.woorden for h in self.hoofdstukken)

    @property
    def afwijkende_hoofdstukken(self) -> list[str]:
        """
        Hoofdstukken die een andere dialoogconventie gebruiken dan de rest.

        Onze Taal laat de keuze vrij maar vraagt consequentheid; dit is die
        controle.
        """
        return [h.hoofdstuk.naam for h in self.hoofdstukken if h.dialoog.wijkt_af]


def analyseer_manuscript(map_pad: str | Path, toon_voortgang: bool = True) -> Manuscript:
    """
    Lees, ontleed en analyseer alle hoofdstukken onder *map_pad*.

    Geeft een Manuscript met een lege hoofdstukkenlijst als er niets te vinden
    was; de aanroeper beslist wat daarmee te doen.
    """
    map_pad = Path(map_pad).expanduser()
    hoofdstukken = laad_hoofdstukken(map_pad)
    manuscript = Manuscript(map_pad=map_pad)

    if not hoofdstukken:
        return manuscript

    # De dialoogconventie is een eigenschap van het manuscript als geheel:
    # eerst manuscriptbreed vaststellen, dan per hoofdstuk toetsen. De tellingen
    # per hoofdstuk opgeteld geven hetzelfde als één telling over het hele boek,
    # en schelen een tweede regex-doorloop over de complete tekst.
    totaal: dict[str, int] = {}
    for hoofdstuk in hoofdstukken:
        for naam, aantal in mod_dialoog.tel_conventies(hoofdstuk.tekst).items():
            totaal[naam] = totaal.get(naam, 0) + aantal
    manuscript.conventie = mod_dialoog.sterkste_conventie(totaal)

    manuscript.taalmodel = huidig_model()

    if toon_voortgang:
        print(f"  {len(hoofdstukken)} hoofdstukken, taalmodel "
              f"{manuscript.taalmodel} wordt geladen ...")

    docs = verwerk(h.tekst for h in hoofdstukken)

    for hoofdstuk, doc in zip(hoofdstukken, docs):
        if toon_voortgang:
            print(f"  · {hoofdstuk.naam}")

        # Woorden en zinnen één keer bepalen en doorgeven: is_woord over elk
        # token is niet gratis, en elke module hieronder had het anders zelf
        # nog eens gedaan.
        woordlijst = woordtokens(doc)
        zinnenlijst = zinlijst(doc)
        woordteksten = [t.text for t in woordlijst]

        schat = woordenschat.analyseer(doc, woordtokens=woordlijst)
        leesbaar = formules.bereken(
            woordteksten,
            len(zinnenlijst),
            moeilijke_woorden=schat.moeilijke_woorden,
        )
        if leesbaar is None:
            continue

        manuscript.hoofdstukken.append(
            HoofdstukAnalyse(
                hoofdstuk=hoofdstuk,
                leesbaarheid=leesbaar,
                woordenschat=schat,
                stijl=stijl.analyseer(
                    doc, zinnen=zinnenlijst, aantal_woorden=len(woordlijst)
                ),
                dialoog=mod_dialoog.analyseer_dialoog(
                    hoofdstuk.tekst, manuscript.conventie
                ),
                tempo=mod_dialoog.analyseer_tempo(doc, zinlijst=zinnenlijst),
            )
        )

    return manuscript


def naar_dataframe(manuscript: Manuscript):
    """
    De kerncijfers als pandas-DataFrame, één rij per hoofdstuk.

    Dit is wat het rapport en de grafieken gebruiken; de volledige uitkomsten
    (voorbeeldzinnen, zeldzame woorden) blijven in het Manuscript zitten.
    """
    import pandas as pd

    rijen = []
    for index, h in enumerate(manuscript.hoofdstukken, start=1):
        rijen.append(
            {
                "hoofdstuk": h.hoofdstuk.naam,
                "volgorde": index,
                "woorden": h.leesbaarheid.woorden,
                "zinnen": h.leesbaarheid.zinnen,
                "flesch_douma": h.leesbaarheid.flesch_douma,
                "leesindex_a": h.leesbaarheid.leesindex_a,
                "fog_nl": h.leesbaarheid.fog_nl,
                "woorden_per_zin": h.leesbaarheid.woorden_per_zin,
                "lange_woorden_pct": h.leesbaarheid.lange_woorden_pct,
                "moeilijk_pct": h.woordenschat.moeilijk_pct,
                "ttr": h.woordenschat.ttr,
                "mtld": h.woordenschat.mtld,
                "passief_pct": h.stijl.passief_pct,
                "tang_pct": h.stijl.tang_pct,
                "naamwoordstijl_per_1000": h.stijl.naamwoordstijl_per_1000,
                "schrapwoorden_per_1000": h.stijl.schrapwoorden_per_1000,
                "dialoog_pct": h.dialoog.dialoog_pct,
                "zinslengte_spreiding": h.tempo.spreiding,
            }
        )

    return pd.DataFrame(rijen)
