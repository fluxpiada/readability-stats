#!/usr/bin/env python3
"""
analyseer.py — de opdrachtregel van de Nederlandse analyse.

    python nl/analyseer.py rapport      ~/Documenten/mijn-boek
    python nl/analyseer.py leesbaarheid ~/Documenten/mijn-boek
    python nl/analyseer.py stijl        ~/Documenten/mijn-boek
    python nl/analyseer.py dialoog      ~/Documenten/mijn-boek
    python nl/analyseer.py woorden      ~/Documenten/mijn-boek

Gemakkelijker is `./nl/run_nl.sh`, dat een menu geeft en de omgeving regelt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leesbaarheid.analyse import Manuscript, analyseer_manuscript, naar_dataframe  # noqa: E402
from leesbaarheid.formules import band  # noqa: E402


def _tabel(df, kolommen: dict[str, str]) -> None:
    """Print een DataFrame als uitgelijnde tekst, zonder extra afhankelijkheden."""
    aanwezig = {k: v for k, v in kolommen.items() if k in df.columns}
    koppen = list(aanwezig.values())

    rijen = []
    for r in df.itertuples():
        rij = []
        for sleutel in aanwezig:
            waarde = getattr(r, sleutel)
            if isinstance(waarde, float):
                rij.append(f"{waarde:.1f}".replace(".", ","))
            else:
                rij.append(str(waarde))
        rijen.append(rij)

    breedtes = [
        max(len(koppen[i]), max((len(r[i]) for r in rijen), default=0))
        for i in range(len(koppen))
    ]

    print("  ".join(k.ljust(b) for k, b in zip(koppen, breedtes)))
    print("  ".join("-" * b for b in breedtes))
    for rij in rijen:
        print("  ".join(c.ljust(b) for c, b in zip(rij, breedtes)))


def toon_leesbaarheid(manuscript: Manuscript) -> None:
    df = naar_dataframe(manuscript)
    df = df.assign(niveau=[band(s)[0] for s in df["flesch_douma"]])
    _tabel(df, {
        "volgorde": "#",
        "hoofdstuk": "Hoofdstuk",
        "woorden": "Woorden",
        "flesch_douma": "Flesch-Douma",
        "leesindex_a": "Leesindex A",
        "fog_nl": "Fog-NL",
        "niveau": "Niveau",
    })
    print()
    print(f"Gemiddeld: {df['flesch_douma'].mean():.1f} "
          f"({band(df['flesch_douma'].mean())[0]}) — "
          f"{band(df['flesch_douma'].mean())[1]}")


def toon_stijl(manuscript: Manuscript) -> None:
    _tabel(naar_dataframe(manuscript), {
        "hoofdstuk": "Hoofdstuk",
        "passief_pct": "Passief %",
        "tang_pct": "Tang %",
        "naamwoordstijl_per_1000": "Naamw./1000",
        "schrapwoorden_per_1000": "Schrapw./1000",
    })
    print()
    print("Alles hierboven is signalering, geen fout. Voorbeelden:")
    for h in manuscript.hoofdstukken:
        for soort, vindplaatsen in h.stijl.voorbeelden.items():
            for v in vindplaatsen[:2]:
                print(f"  [{soort}] {h.hoofdstuk.naam}: {v.zin}")
                print(f"      {v.detail}")


def toon_dialoog(manuscript: Manuscript) -> None:
    _tabel(naar_dataframe(manuscript), {
        "hoofdstuk": "Hoofdstuk",
        "dialoog_pct": "Dialoog %",
        "woorden_per_zin": "Zinslengte",
        "zinslengte_spreiding": "Spreiding",
    })
    print()
    print(f"Dialoogconventie in dit manuscript: {manuscript.conventie or 'geen gevonden'}")
    afwijkend = manuscript.afwijkende_hoofdstukken
    if afwijkend:
        print("Afwijkend van de rest: " + ", ".join(afwijkend))
        print("Onze Taal laat de keuze vrij, maar vraagt wel consequentheid.")
    else:
        print("De aanhalingstekens zijn consequent door het hele manuscript.")


def toon_woorden(manuscript: Manuscript) -> None:
    _tabel(naar_dataframe(manuscript), {
        "hoofdstuk": "Hoofdstuk",
        "moeilijk_pct": "Moeilijk %",
        "ttr": "TTR",
        "mtld": "MTLD",
    })
    print()
    print("Zeldzaamste woorden per hoofdstuk:")
    for h in manuscript.hoofdstukken:
        woorden = ", ".join(w for w, _ in h.woordenschat.zeldzaamste[:8])
        print(f"  {h.hoofdstuk.naam}: {woorden or '—'}")
        if h.woordenschat.samenstellingen_gered:
            print(f"      ({h.woordenschat.samenstellingen_gered} samenstellingen "
                  f"niet als moeilijk geteld)")


def toon_rapport(manuscript: Manuscript, map_uit: str | None) -> None:
    from leesbaarheid.rapport import maak_rapport

    doel = maak_rapport(manuscript, Path(map_uit) if map_uit else None)
    print()
    print(f"Rapport geschreven naar: {doel}")
    for bestand in sorted(doel.iterdir()):
        print(f"  {bestand.name}")


OPDRACHTEN = {
    "rapport": None,
    "leesbaarheid": toon_leesbaarheid,
    "stijl": toon_stijl,
    "dialoog": toon_dialoog,
    "woorden": toon_woorden,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Leesbaarheids- en stijlanalyse voor Nederlandse manuscripten.",
    )
    parser.add_argument("opdracht", choices=sorted(OPDRACHTEN), help="wat u wilt zien")
    parser.add_argument("map", help="map met .md- of .docx-bestanden")
    parser.add_argument("uitvoer", nargs="?", default=None,
                        help="map voor het rapport (alleen bij 'rapport')")
    argumenten = parser.parse_args(argv)

    map_pad = Path(argumenten.map).expanduser()
    if not map_pad.is_dir():
        print(f"Dit is geen map: {map_pad}")
        return 1

    print(f"Manuscript: {map_pad}")
    manuscript = analyseer_manuscript(map_pad)

    if not manuscript.hoofdstukken:
        print("Geen .md- of .docx-bestanden met tekst gevonden.")
        return 1

    print()
    if argumenten.opdracht == "rapport":
        toon_rapport(manuscript, argumenten.uitvoer)
    else:
        OPDRACHTEN[argumenten.opdracht](manuscript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
