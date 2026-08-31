"""
tekst.py — manuscriptbestanden inlezen en in hoofdstukken opdelen.

Invoercontract (zie nl/README.md):

* `.md` en `.docx`, recursief onder de opgegeven map;
* mappen met een onderdeel `draft` of `klad` in het pad worden overgeslagen;
* volgorde = alfabetisch op volledig pad, dus `01_`, `02_` … werkt zoals verwacht;
* een bestand is één hoofdstuk, tenzij er twee of meer Nederlandse
  hoofdstukkoppen in staan — dan splitsen we daarop.

Twee dingen doen we bewust anders dan de Engelse variant in `read_stats.py`:

1. **Typografie wordt genormaliseerd, niet weggegooid.** De krulapostrof `’`
   wordt een rechte `'`, zodat "z'n" één token blijft in plaats van twee. De
   aanhalingstekens `„ " " « »` blijven juist staan: `dialoog.py` heeft ze nodig
   om te bepalen welke dialoogconventie het manuscript hanteert.
2. **Streepjes aan het begin van een regel blijven staan.** De Engelse
   markdown-stripper haalt `-`, `*` en `+` aan het regelbegin weg omdat het
   opsommingstekens zijn. In Nederlands proza is een streepje aan het regelbegin
   veel vaker een dialoogstreepje, en dat weggooien kost ons de dialoogherkenning.
   Opsommingen in een manuscript zijn zeldzaam; dialoog niet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import docx
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    DOCX_BESCHIKBAAR = True
except ImportError:
    DOCX_BESCHIKBAAR = False


ONDERSTEUNDE_EXTENSIES = {".md", ".markdown", ".txt", ".docx"}

# Mapnamen die niet meetellen: werk in uitvoering.
OVERSLAAN = {"draft", "drafts", "klad", "kladversie", "oud", "archief"}


@dataclass(frozen=True)
class Hoofdstuk:
    """Eén hoofdstuk: de tekst plus waar hij vandaan komt."""

    naam: str
    tekst: str
    bron: Path
    volgorde: int


# ---------------------------------------------------------------
# Normalisatie
# ---------------------------------------------------------------

# Krulapostrofs -> rechte apostrof. Dit is de fout die in de Engelse versie
# zichtbaar is in converted_txt/: "didn’t" viel uiteen in "didn" en "t".
_APOSTROFS = str.maketrans({"’": "'", "‘": "'", "‛": "'", "ʼ": "'"})


def normaliseer(tekst: str) -> str:
    """Maak de typografie voorspelbaar zonder dialoogtekens te verliezen."""
    tekst = tekst.translate(_APOSTROFS)
    tekst = tekst.replace("…", "...")          # beletselteken
    tekst = tekst.replace(" ", " ")            # harde spatie
    tekst = re.sub(r"[ \t]+", " ", tekst)
    tekst = re.sub(r"\n{3,}", "\n\n", tekst)
    return tekst.strip()


def strip_markdown(md: str) -> str:
    """
    Markdown -> platte tekst.

    Koppen (`#`) worden tot gewone regels teruggebracht, maar de kopregel zelf
    blijft staan: `splits_hoofdstukken` heeft hem nodig. Streepjes aan het
    regelbegin blijven onaangeroerd (zie de moduledocstring).
    """
    tekst = md
    tekst = re.sub(r"```.*?```", "", tekst, flags=re.DOTALL)    # codeblokken
    tekst = re.sub(r"`([^`]*)`", r"\1", tekst)                  # inline code
    tekst = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", tekst)          # afbeeldingen
    tekst = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", tekst)      # links -> label
    tekst = re.sub(r"^\s{0,3}>[ \t]?", "", tekst, flags=re.M)   # citaatblokken
    tekst = re.sub(r"^\s{0,3}(#{1,6})\s*", r"\1 ", tekst, flags=re.M)
    tekst = re.sub(r"^\s*([-*_])\s*\1\s*\1[\s\1]*$", "", tekst, flags=re.M)  # ---
    tekst = re.sub(r"(?<!\w)([*_]{1,3})(\S.*?\S|\S)\1(?!\w)", r"\2", tekst)  # nadruk
    return tekst


# ---------------------------------------------------------------
# .docx
# ---------------------------------------------------------------

# Een Nederlandse Word-installatie noemt kopstijlen "Kop 1", een Engelse
# "Heading 1". Beide moeten werken, anders mist hoofdstukdetectie precies bij
# de gebruiker voor wie deze tool bedoeld is.
_KOPSTIJL = re.compile(r"^(kop|heading|titel|title)\s*(\d)?", re.I)


def _blokken(document):
    """Alinea's en tabellen in documentvolgorde, niet eerst alle alinea's."""
    body = document.element.body
    for kind in body.iterchildren():
        if isinstance(kind, CT_P):
            yield Paragraph(kind, document)
        elif isinstance(kind, CT_Tbl):
            yield Table(kind, document)


def lees_docx(pad: Path) -> str:
    """
    Platte tekst uit een .docx.

    Neemt ook tabelcellen mee, en zet Word-koppen om naar markdown-koppen zodat
    hoofdstukdetectie voor .md en .docx identiek werkt.
    """
    if not DOCX_BESCHIKBAAR:
        raise ImportError("python-docx ontbreekt. Draai: uv sync")

    document = docx.Document(str(pad))
    regels: list[str] = []

    for blok in _blokken(document):
        if isinstance(blok, Table):
            for rij in blok.rows:
                cellen = [c.text.strip() for c in rij.cells if c.text.strip()]
                if cellen:
                    regels.append(" | ".join(cellen))
            continue

        inhoud = blok.text.strip()
        if not inhoud:
            regels.append("")
            continue

        stijl = (blok.style.name if blok.style is not None else "") or ""
        treffer = _KOPSTIJL.match(stijl.strip())
        if treffer:
            niveau = int(treffer.group(2) or 1)
            regels.append(f"{'#' * min(niveau, 6)} {inhoud}")
        else:
            regels.append(inhoud)

    return "\n".join(regels)


# ---------------------------------------------------------------
# Hoofdstukdetectie
# ---------------------------------------------------------------

# Expliciete Nederlandse hoofdstukaanduidingen. Deze wegen zwaarder dan
# markdown-koppen: een auteur die "Hoofdstuk 3" schrijft, bedoelt een hoofdstuk.
_HOOFDSTUKWOORDEN = (
    r"hoofdstuk|deel|proloog|epiloog|voorwoord|nawoord|naschrift|"
    r"dankwoord|verantwoording|intermezzo|inleiding"
)

_EXPLICIETE_KOP = re.compile(
    rf"^\s*(?:#{{1,6}}\s*)?((?:{_HOOFDSTUKWOORDEN})\b[^\n]*)$",
    re.I | re.M,
)

_MARKDOWN_KOP = re.compile(r"^\s*(#{1,2})\s+([^\n]+)$", re.M)


def _naam_van_kop(regel: str) -> str:
    return re.sub(r"^#+\s*", "", regel).strip(" #*_")


def splits_hoofdstukken(tekst: str) -> list[tuple[str, str]]:
    """
    Deel *tekst* op in (kop, inhoud). Eén element als er niets te splitsen valt.

    Alleen splitsen bij twee of meer koppen: bij één kop is dat gewoon de titel
    van het bestand, en dan is het bestand zelf het hoofdstuk.
    """
    for patroon in (_EXPLICIETE_KOP, _MARKDOWN_KOP):
        treffers = list(patroon.finditer(tekst))
        if len(treffers) < 2:
            continue

        stukken: list[tuple[str, str]] = []
        aanhef = tekst[: treffers[0].start()].strip()
        if aanhef:
            stukken.append(("(begin)", aanhef))

        for i, treffer in enumerate(treffers):
            einde = treffers[i + 1].start() if i + 1 < len(treffers) else len(tekst)
            kop = _naam_van_kop(treffer.group(0))
            inhoud = tekst[treffer.end() : einde].strip()
            if inhoud:
                stukken.append((kop, inhoud))

        if len(stukken) >= 2:
            return stukken

    return [("", tekst)]


# ---------------------------------------------------------------
# Laden
# ---------------------------------------------------------------

def _bestanden(map_pad: Path) -> list[Path]:
    return sorted(
        p
        for p in map_pad.rglob("*")
        if p.is_file()
        and p.suffix.lower() in ONDERSTEUNDE_EXTENSIES
        and not any(deel.lower() in OVERSLAAN for deel in p.parts)
        and not p.name.startswith((".", "~$"))
    )


def lees_bestand(pad: Path) -> str:
    """Platte, genormaliseerde tekst uit één bestand."""
    if pad.suffix.lower() == ".docx":
        ruw = lees_docx(pad)
    else:
        ruw = pad.read_text(encoding="utf-8", errors="replace")
        if pad.suffix.lower() != ".txt":
            ruw = strip_markdown(ruw)
    return normaliseer(ruw)


def laad_hoofdstukken(map_pad: str | Path) -> list[Hoofdstuk]:
    """
    Laad alle hoofdstukken onder *map_pad*, in leesvolgorde.

    Levert een lege lijst als er niets bruikbaars staat; de aanroeper beslist
    wat daarmee te doen.
    """
    basis = Path(map_pad).expanduser()
    hoofdstukken: list[Hoofdstuk] = []

    for pad in _bestanden(basis):
        try:
            tekst = lees_bestand(pad)
        except Exception as fout:                  # onleesbaar bestand blokkeert niet
            print(f"  overgeslagen: {pad.name} ({fout})")
            continue

        if not tekst.strip():
            continue

        stukken = splits_hoofdstukken(tekst)
        for kop, inhoud in stukken:
            if not inhoud.strip():
                continue
            naam = kop or pad.stem
            if len(stukken) > 1 and kop:
                naam = f"{pad.stem} — {kop}" if len(stukken) > 2 else kop
            hoofdstukken.append(
                Hoofdstuk(
                    naam=naam,
                    tekst=inhoud,
                    bron=pad,
                    volgorde=len(hoofdstukken) + 1,
                )
            )

    return hoofdstukken
