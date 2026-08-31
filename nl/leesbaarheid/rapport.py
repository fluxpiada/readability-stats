"""
rapport.py — het rapport in markdown en PDF, plus de grafieken.

Inhoud staat één keer gedefinieerd (in `teksten.py`) en wordt door beide
uitvoervormen gebruikt, zodat markdown en PDF niet uiteen kunnen lopen.

**Lettertype.** De PDF registreert DejaVuSans als TrueType-font. Dat is geen
opsmuk: reportlab's ingebouwde Helvetica kent alleen WinAnsi en laat alles
daarbuiten stilzwijgend weg — dus precies de lage aanhalingstekens „ ", het
gedachtestreepje – en letters als é en ë die een Nederlands rapport nodig heeft.
De Engelse versie omzeilt dat door kopteksten bewust ASCII te houden; wij lossen
het op. DejaVuSans zit al in de installatie via matplotlib, dus het kost geen
extra download.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from . import teksten
from .analyse import Manuscript, naar_dataframe
from .formules import band

# matplotlib schrijft anders naar de home-map van de gebruiker
_CACHE = (Path(__file__).resolve().parents[2] / ".matplotlib_cache")
_CACHE.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE))

DEJAVU = "DejaVuSans"


# ---------------------------------------------------------------
# Hulpjes
# ---------------------------------------------------------------

def fmt(waarde, decimalen: int = 1) -> str:
    """Getal netjes, met een streepje voor wat ontbreekt."""
    if waarde is None:
        return "—"
    try:
        if waarde != waarde:            # NaN
            return "—"
    except TypeError:
        return "—"
    if isinstance(waarde, int):
        return f"{waarde:,}".replace(",", ".")
    return f"{waarde:.{decimalen}f}".replace(".", ",")


def md_tabel(koppen: list[str], rijen: list[list[str]]) -> str:
    regels = ["| " + " | ".join(koppen) + " |",
              "|" + "|".join("---" for _ in koppen) + "|"]
    regels += ["| " + " | ".join(rij) + " |" for rij in rijen]
    return "\n".join(regels)


# ---------------------------------------------------------------
# Tabellen
# ---------------------------------------------------------------

def tabellen(manuscript: Manuscript) -> dict[str, tuple[list[str], list[list[str]]]]:
    """Alle tabellen als kant-en-klare tekst, zodat md en PDF identiek zijn."""
    df = naar_dataframe(manuscript)
    uit: dict[str, tuple[list[str], list[list[str]]]] = {}

    uit["per_hoofdstuk"] = (
        ["#", "Hoofdstuk", "Woorden", "Flesch-Douma", "Niveau", "Leesindex A", "Fog-NL"],
        [
            [
                str(r.volgorde),
                r.hoofdstuk,
                fmt(int(r.woorden)),
                fmt(r.flesch_douma),
                band(r.flesch_douma)[0],
                fmt(r.leesindex_a),
                fmt(r.fog_nl),
            ]
            for r in df.itertuples()
        ],
    )

    zwaar = df.sort_values("flesch_douma")
    uit["zwaarste"] = (
        ["Hoofdstuk", "Flesch-Douma", "Woorden/zin", "Lange woorden %", "Moeilijk %"],
        [
            [
                r.hoofdstuk,
                fmt(r.flesch_douma),
                fmt(r.woorden_per_zin),
                fmt(r.lange_woorden_pct),
                fmt(r.moeilijk_pct),
            ]
            for r in zwaar.itertuples()
        ],
    )

    uit["woordenschat"] = (
        ["Hoofdstuk", "Moeilijk %", "TTR", "MTLD", "Zeldzaamste woorden"],
        [
            [
                h.hoofdstuk.naam,
                fmt(h.woordenschat.moeilijk_pct),
                fmt(h.woordenschat.ttr, 2),
                fmt(h.woordenschat.mtld),
                ", ".join(w for w, _ in h.woordenschat.zeldzaamste[:6]) or "—",
            ]
            for h in manuscript.hoofdstukken
        ],
    )

    uit["stijl"] = (
        ["Hoofdstuk", "Passief %", "Tang %", "Naamw./1000", "Schrapw./1000"],
        [
            [
                h.hoofdstuk.naam,
                fmt(h.stijl.passief_pct),
                fmt(h.stijl.tang_pct),
                fmt(h.stijl.naamwoordstijl_per_1000),
                fmt(h.stijl.schrapwoorden_per_1000),
            ]
            for h in manuscript.hoofdstukken
        ],
    )

    uit["dialoog"] = (
        ["Hoofdstuk", "Dialoog %", "Conventie", "Zinslengte", "Spreiding"],
        [
            [
                h.hoofdstuk.naam,
                fmt(h.dialoog.dialoog_pct),
                h.dialoog.conventie or "—",
                fmt(h.tempo.gemiddelde),
                fmt(h.tempo.spreiding),
            ]
            for h in manuscript.hoofdstukken
        ],
    )

    return uit


def samenvatting(manuscript: Manuscript) -> list[tuple[str, str]]:
    df = naar_dataframe(manuscript)
    moeilijkste = df.loc[df["flesch_douma"].idxmin()]
    makkelijkste = df.loc[df["flesch_douma"].idxmax()]

    regels = [
        ("Map", str(manuscript.map_pad)),
        ("Hoofdstukken", fmt(len(manuscript.hoofdstukken))),
        ("Woorden totaal", fmt(manuscript.woorden)),
        ("Flesch-Douma gemiddeld", fmt(df["flesch_douma"].mean())),
        ("Leesniveau", band(df["flesch_douma"].mean())[1]),
        ("Zwaarste hoofdstuk", f"{moeilijkste.hoofdstuk} ({fmt(moeilijkste.flesch_douma)})"),
        ("Lichtste hoofdstuk", f"{makkelijkste.hoofdstuk} ({fmt(makkelijkste.flesch_douma)})"),
        ("Gemiddelde zinslengte", f"{fmt(df['woorden_per_zin'].mean())} woorden"),
        ("Lijdende vorm gemiddeld", f"{fmt(df['passief_pct'].mean())} % van de zinnen"),
        ("Dialoogaandeel gemiddeld", f"{fmt(df['dialoog_pct'].mean())} %"),
        ("Dialoogconventie", manuscript.conventie or "geen dialoog gevonden"),
    ]

    afwijkend = manuscript.afwijkende_hoofdstukken
    if afwijkend:
        regels.append(("Afwijkende aanhalingstekens", ", ".join(afwijkend)))

    return regels


# ---------------------------------------------------------------
# Grafieken
# ---------------------------------------------------------------

def _stel_matplotlib_in():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def leesbaarheidscurve(manuscript: Manuscript, pad: Path) -> Path:
    """
    Flesch-Douma over de hoofdstukken, met de interpretatiebanden eronder.

    Geen enkele streeplijn zoals de Engelse versie ('readable threshold 60'):
    voor fictie bestaat die grens niet. De banden zijn context, geen norm.
    """
    plt = _stel_matplotlib_in()
    df = naar_dataframe(manuscript)

    fig, ax = plt.subplots(figsize=(10, 5))

    banden = [
        (90, 100, "#e8f5e9", "zeer makkelijk"),
        (70, 90, "#f1f8e9", "makkelijk"),
        (60, 70, "#fffde7", "standaard"),
        (50, 60, "#fff3e0", "vrij moeilijk"),
        (0, 50, "#fbe9e7", "moeilijk"),
    ]
    for onder, boven, kleur, _ in banden:
        ax.axhspan(onder, boven, color=kleur, zorder=0)

    ax.plot(df["volgorde"], df["flesch_douma"], marker="o",
            linewidth=1.8, color="#37474f", zorder=3)

    ax.set_title("Leesbaarheid per hoofdstuk (Flesch-Douma)")
    ax.set_xlabel("Hoofdstuk")
    ax.set_ylabel("Flesch-Douma")
    ax.set_xticks(df["volgorde"])

    laag = max(0, df["flesch_douma"].min() - 15)
    hoog = min(105, df["flesch_douma"].max() + 15)
    ax.set_ylim(laag, hoog)
    ax.grid(axis="y", alpha=0.25, zorder=2)

    # Bandnamen binnen het assenvlak zetten, en alleen die ook echt zichtbaar
    # zijn: x in assenfractie, y in datacoördinaten.
    for onder, boven, _, label in banden:
        midden = (max(onder, laag) + min(boven, hoog)) / 2
        if laag < midden < hoog and min(boven, hoog) - max(onder, laag) > 4:
            ax.text(0.995, midden, label, transform=ax.get_yaxis_transform(),
                    fontsize=7, color="#90a4ae", va="center", ha="right", zorder=4)

    fig.tight_layout()
    fig.savefig(pad, dpi=150)
    plt.close(fig)
    return pad


def dialoogcurve(manuscript: Manuscript, pad: Path) -> Path:
    """Dialoogaandeel en zinslengtespreiding naast elkaar."""
    plt = _stel_matplotlib_in()
    df = naar_dataframe(manuscript)

    fig, (boven, onder) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    boven.bar(df["volgorde"], df["dialoog_pct"], color="#5c6bc0")
    boven.set_ylabel("Dialoog (%)")
    boven.set_title("Dialoogaandeel en ritme per hoofdstuk")
    boven.grid(axis="y", alpha=0.25)

    onder.plot(df["volgorde"], df["woorden_per_zin"], marker="o",
               label="gemiddelde zinslengte", color="#37474f")
    onder.plot(df["volgorde"], df["zinslengte_spreiding"], marker="s",
               linestyle="--", label="spreiding", color="#ef6c00")
    onder.set_xlabel("Hoofdstuk")
    onder.set_ylabel("Woorden")
    onder.set_xticks(df["volgorde"])
    onder.legend(fontsize=8)
    onder.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(pad, dpi=150)
    plt.close(fig)
    return pad


# ---------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------

def schrijf_markdown(manuscript: Manuscript, map_uit: Path, grafieken: list[str]) -> Path:
    tab = tabellen(manuscript)
    regels: list[str] = [
        f"# {teksten.TITEL}",
        "",
        f"*{teksten.ONDERTITEL}*",
        "",
        f"Gemaakt op {datetime.now():%d-%m-%Y om %H:%M}.",
        "",
        "## Samenvatting",
        "",
        md_tabel(["", ""], [[k, v] for k, v in samenvatting(manuscript)]),
        "",
        teksten.CAVEAT,
        "",
    ]

    for naam in grafieken:
        regels += [f"![{naam}]({naam})", ""]

    for sleutel, titel, blurb in teksten.SECTIES:
        koppen, rijen = tab[sleutel]
        regels += [f"## {titel}", "", blurb, "", md_tabel(koppen, rijen), ""]

    # Vindplaatsen: de voorbeelden zijn het punt, niet de percentages.
    regels += ["## Vindplaatsen", "",
               "Voorbeelden uit de tekst zelf. Lees deze voordat u iets met de "
               "percentages doet — of iets een probleem is, bepaalt u.", ""]

    etiketten = {
        "passief": "Lijdende vorm",
        "tangconstructie": "Tangconstructies",
        "naamwoordstijl": "Naamwoordstijl",
        "schrapwoorden": "Schrapwoorden",
    }
    for h in manuscript.hoofdstukken:
        gevonden = {k: v for k, v in h.stijl.voorbeelden.items() if v}
        if not gevonden:
            continue
        regels += [f"### {h.hoofdstuk.naam}", ""]
        for soort, vindplaatsen in gevonden.items():
            regels.append(f"**{etiketten.get(soort, soort)}**")
            regels.append("")
            for v in vindplaatsen[:5]:
                regels.append(f"- {v.zin}  \n  *{v.detail}*")
            regels.append("")

    regels += ["## Begrippenlijst en verantwoording", ""]
    for maat in teksten.MATEN:
        regels += [
            f"### {maat.naam}",
            "",
            f"**Wat het meet.** {maat.wat}",
            "",
            f"**Waar het vandaan komt.** {maat.bron}",
            "",
            f"**Hoe wij het berekenen.** {maat.hoe}",
            "",
            f"**Beperkingen.** {maat.beperking}",
            "",
        ]

    regels += ["## Voorbehoud", ""]
    for kop, tekst in teksten.VOORBEHOUD:
        regels += [f"**{kop}.** {tekst}", ""]

    regels += ["## Literatuur", ""]
    for verwijzing, url in teksten.LITERATUUR:
        regels.append(f"- {verwijzing} <{url}>")
    regels.append("")

    pad = map_uit / "rapport.md"
    pad.write_text("\n".join(regels), encoding="utf-8")
    return pad


# ---------------------------------------------------------------
# PDF
# ---------------------------------------------------------------

def _registreer_fonts() -> bool:
    """
    Zet DejaVuSans klaar voor reportlab.

    Zonder dit verdwijnen „ " – é ë stilzwijgend uit de PDF.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if DEJAVU in pdfmetrics.getRegisteredFontNames():
        return True

    try:
        import matplotlib
        ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        pdfmetrics.registerFont(TTFont(DEJAVU, str(ttf / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(f"{DEJAVU}-Bold", str(ttf / "DejaVuSans-Bold.ttf")))
        from reportlab.lib.fonts import addMapping
        addMapping(DEJAVU, 0, 0, DEJAVU)
        addMapping(DEJAVU, 1, 0, f"{DEJAVU}-Bold")
        return True
    except Exception as fout:
        print(f"  let op: Unicode-lettertype niet geladen ({fout});")
        print("  aanhalingstekens en accenten kunnen uit de PDF wegvallen.")
        return False


def schrijf_pdf(manuscript: Manuscript, map_uit: Path, grafieken: list[Path]) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    unicode_ok = _registreer_fonts()
    basis = DEJAVU if unicode_ok else "Helvetica"
    vet = f"{DEJAVU}-Bold" if unicode_ok else "Helvetica-Bold"

    pad = map_uit / "rapport.pdf"
    doc = SimpleDocTemplate(
        str(pad), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=teksten.TITEL, author="readability-stats",
    )
    breedte = doc.width

    vellen = getSampleStyleSheet()
    stijl_titel = ParagraphStyle("Titel", parent=vellen["Title"], fontName=vet, fontSize=20)
    stijl_kop = ParagraphStyle("Kop", parent=vellen["Heading2"], fontName=vet,
                               fontSize=13, spaceBefore=14, textColor=colors.HexColor("#37474f"))
    stijl_subkop = ParagraphStyle("Subkop", parent=vellen["Heading3"], fontName=vet, fontSize=10.5)
    stijl_tekst = ParagraphStyle("Tekst", parent=vellen["BodyText"], fontName=basis,
                                 fontSize=9, leading=13, alignment=TA_LEFT)
    stijl_klein = ParagraphStyle("Klein", parent=stijl_tekst, fontSize=8,
                                 textColor=colors.HexColor("#546e7a"))

    verhaal = [Paragraph(teksten.TITEL, stijl_titel),
               Paragraph(teksten.ONDERTITEL, stijl_klein),
               Spacer(1, 6),
               Paragraph(f"Gemaakt op {datetime.now():%d-%m-%Y om %H:%M}.", stijl_klein),
               Spacer(1, 12)]

    def tabel(koppen, rijen, kolombreedtes=None):
        data = [[Paragraph(f"<b>{k}</b>", stijl_klein) for k in koppen]]
        data += [[Paragraph(str(c), stijl_klein) for c in rij] for rij in rijen]
        t = Table(data, colWidths=kolombreedtes, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), basis),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cfd8dc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f7f8")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    # Samenvatting
    verhaal.append(Paragraph("Samenvatting", stijl_kop))
    verhaal.append(tabel(["", ""], samenvatting(manuscript),
                         kolombreedtes=[breedte * 0.35, breedte * 0.65]))
    verhaal.append(Spacer(1, 8))
    verhaal.append(Paragraph(teksten.CAVEAT, stijl_klein))

    # Grafieken
    for grafiek in grafieken:
        breedte_px, hoogte_px = ImageReader(str(grafiek)).getSize()
        schaal = breedte / breedte_px
        verhaal.append(Spacer(1, 10))
        verhaal.append(Image(str(grafiek), width=breedte, height=hoogte_px * schaal))

    # Tabelsecties
    tab = tabellen(manuscript)
    for sleutel, titel, blurb in teksten.SECTIES:
        koppen, rijen = tab[sleutel]
        verhaal.append(PageBreak())
        verhaal.append(Paragraph(titel, stijl_kop))
        verhaal.append(Paragraph(blurb, stijl_klein))
        verhaal.append(Spacer(1, 6))
        verhaal.append(tabel(koppen, rijen))

    # Vindplaatsen
    etiketten = {
        "passief": "Lijdende vorm",
        "tangconstructie": "Tangconstructies",
        "naamwoordstijl": "Naamwoordstijl",
        "schrapwoorden": "Schrapwoorden",
    }
    verhaal.append(PageBreak())
    verhaal.append(Paragraph("Vindplaatsen", stijl_kop))
    verhaal.append(Paragraph(
        "Voorbeelden uit de tekst zelf. Lees deze voordat u iets met de "
        "percentages doet — of iets een probleem is, bepaalt u.", stijl_klein))

    for h in manuscript.hoofdstukken:
        gevonden = {k: v for k, v in h.stijl.voorbeelden.items() if v}
        if not gevonden:
            continue
        blok = [Paragraph(h.hoofdstuk.naam, stijl_subkop)]
        for soort, vindplaatsen in gevonden.items():
            blok.append(Paragraph(f"<b>{etiketten.get(soort, soort)}</b>", stijl_klein))
            for v in vindplaatsen[:4]:
                blok.append(Paragraph(v.zin, stijl_tekst))
                blok.append(Paragraph(f"<i>{v.detail}</i>", stijl_klein))
        verhaal.append(Spacer(1, 8))
        verhaal.append(KeepTogether(blok))

    # Verantwoording
    verhaal.append(PageBreak())
    verhaal.append(Paragraph("Begrippenlijst en verantwoording", stijl_kop))
    for maat in teksten.MATEN:
        blok = [
            Paragraph(maat.naam, stijl_subkop),
            Paragraph(f"<b>Wat het meet.</b> {maat.wat}", stijl_tekst),
            Paragraph(f"<b>Waar het vandaan komt.</b> {maat.bron.replace(chr(10), '<br/>')}",
                      stijl_tekst),
            Paragraph(f"<b>Hoe wij het berekenen.</b> {maat.hoe}", stijl_tekst),
            Paragraph(f"<b>Beperkingen.</b> {maat.beperking}", stijl_tekst),
            Spacer(1, 6),
        ]
        verhaal.append(KeepTogether(blok))

    verhaal.append(PageBreak())
    verhaal.append(Paragraph("Voorbehoud", stijl_kop))
    for kop, tekst in teksten.VOORBEHOUD:
        verhaal.append(Paragraph(f"<b>{kop}.</b> {tekst}", stijl_tekst))
        verhaal.append(Spacer(1, 4))

    verhaal.append(Paragraph("Literatuur", stijl_kop))
    for verwijzing, url in teksten.LITERATUUR:
        verhaal.append(Paragraph(f"{verwijzing}<br/><font size=7>{url}</font>", stijl_klein))
        verhaal.append(Spacer(1, 3))

    verhaal.append(Spacer(1, 8))
    verhaal.append(Paragraph("Licenties van gebruikte bronnen", stijl_subkop))
    for wat, licentie in teksten.LICENTIES:
        verhaal.append(Paragraph(f"{wat}: {licentie}", stijl_klein))

    doc.build(verhaal)
    return pad


# ---------------------------------------------------------------
# Momentopnames
# ---------------------------------------------------------------

def nieuwe_map(wortel: Path) -> Path:
    wortel.mkdir(parents=True, exist_ok=True)
    basis = datetime.now().strftime("%Y-%m-%d-%H%M")
    map_uit = wortel / basis
    teller = 2
    while map_uit.exists():
        map_uit = wortel / f"{basis}-{teller}"
        teller += 1
    map_uit.mkdir()
    return map_uit


def schrijf_samenvatting_json(manuscript: Manuscript, map_uit: Path) -> Path:
    df = naar_dataframe(manuscript)
    gegevens = {
        "gemaakt": datetime.now().isoformat(timespec="seconds"),
        "map": str(manuscript.map_pad),
        "hoofdstukken": len(manuscript.hoofdstukken),
        "woorden": int(manuscript.woorden),
        "flesch_douma_gemiddeld": round(float(df["flesch_douma"].mean()), 2),
        "leesindex_a_gemiddeld": round(float(df["leesindex_a"].mean()), 2),
        "moeilijk_pct_gemiddeld": round(float(df["moeilijk_pct"].mean()), 2),
        "passief_pct_gemiddeld": round(float(df["passief_pct"].mean()), 2),
        "dialoog_pct_gemiddeld": round(float(df["dialoog_pct"].mean()), 2),
        "conventie": manuscript.conventie,
    }
    pad = map_uit / "samenvatting.json"
    pad.write_text(json.dumps(gegevens, indent=2, ensure_ascii=False), encoding="utf-8")
    return pad


def werk_laatste_bij(wortel: Path, map_uit: Path) -> None:
    koppeling = wortel / "laatste"
    try:
        if koppeling.is_symlink() or koppeling.exists():
            koppeling.unlink()
        koppeling.symlink_to(map_uit.name)
    except OSError:
        pass            # symlinks werken niet overal; geen reden om te stoppen


def schrijf_index(wortel: Path) -> Path | None:
    """Overzicht van alle runs, met het verschil ten opzichte van de vorige."""
    opnames = []
    for pad in sorted(wortel.glob("*/samenvatting.json")):
        # 'laatste' is een snelkoppeling naar een van de mappen hieronder; die
        # zou anders als aparte run in het overzicht komen.
        if pad.parent.is_symlink():
            continue
        try:
            opnames.append((pad.parent.name, json.loads(pad.read_text(encoding="utf-8"))))
        except Exception:
            continue

    if not opnames:
        return None

    regels = ["# Rapporten", "", "Elke run staat in een eigen map.", "",
              "| Run | Hoofdstukken | Woorden | Flesch-Douma | Verschil |",
              "|---|---|---|---|---|"]

    vorige = None
    for naam, gegevens in opnames:
        score = gegevens.get("flesch_douma_gemiddeld")
        verschil = "—" if vorige is None or score is None else f"{score - vorige:+.1f}".replace(".", ",")
        regels.append(
            f"| [{naam}]({naam}/rapport.md) | {gegevens.get('hoofdstukken', '—')} "
            f"| {gegevens.get('woorden', '—')} | {fmt(score)} | {verschil} |"
        )
        if score is not None:
            vorige = score

    pad = wortel / "index.md"
    pad.write_text("\n".join(regels) + "\n", encoding="utf-8")
    return pad


# ---------------------------------------------------------------
# Alles samen
# ---------------------------------------------------------------

def maak_rapport(manuscript: Manuscript, map_uit: Path | None = None,
                 wortel: Path | None = None) -> Path:
    """
    Schrijf rapport.md, rapport.pdf en de grafieken.

    Zonder *map_uit* wordt een momentopname gemaakt onder `rapporten/`.
    """
    if map_uit is None:
        wortel = wortel or Path("rapporten")
        map_uit = nieuwe_map(wortel)
        momentopname = True
    else:
        map_uit = Path(map_uit)
        map_uit.mkdir(parents=True, exist_ok=True)
        momentopname = False

    grafieken = [
        leesbaarheidscurve(manuscript, map_uit / "leesbaarheid.png"),
        dialoogcurve(manuscript, map_uit / "dialoog_en_tempo.png"),
    ]

    schrijf_markdown(manuscript, map_uit, [g.name for g in grafieken])
    schrijf_pdf(manuscript, map_uit, grafieken)

    if momentopname:
        schrijf_samenvatting_json(manuscript, map_uit)
        werk_laatste_bij(wortel, map_uit)
        schrijf_index(wortel)

    return map_uit
