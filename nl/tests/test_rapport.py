"""
Rapportage van begin tot eind, op het meegeleverde voorbeeldmanuscript.

De belangrijkste test hier is de laatste: staan de Nederlandse leestekens
daadwerkelijk in de PDF? Zonder geregistreerd Unicode-lettertype laat reportlab
ze stilzwijgend weg, en dan is er niets aan te zien behalve ontbrekende tekens.
"""

import json
from pathlib import Path

import pytest

from leesbaarheid.analyse import analyseer_manuscript, naar_dataframe
from leesbaarheid.rapport import maak_rapport, schrijf_index

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def manuscript():
    return analyseer_manuscript(FIXTURES, toon_voortgang=False)


@pytest.fixture(scope="module")
def rapportmap(manuscript, tmp_path_factory):
    doel = tmp_path_factory.mktemp("rapport")
    return maak_rapport(manuscript, map_uit=doel)


def test_alle_hoofdstukken_geanalyseerd(manuscript):
    assert len(manuscript.hoofdstukken) == 4
    assert manuscript.woorden > 300


def test_bestanden_bestaan(rapportmap):
    for naam in ("rapport.md", "rapport.pdf", "leesbaarheid.png", "dialoog_en_tempo.png"):
        bestand = rapportmap / naam
        assert bestand.exists(), f"{naam} ontbreekt"
        assert bestand.stat().st_size > 0


def test_markdown_bevat_de_verantwoording(rapportmap):
    tekst = (rapportmap / "rapport.md").read_text(encoding="utf-8")
    # elke maat hoort met bron en beperking in het rapport te staan
    assert "Waar het vandaan komt" in tekst
    assert "Beperkingen" in tekst
    assert "Douma" in tekst and "Brouwer" in tekst
    assert "Onze Taal" in tekst
    # en de eerlijkheid over wat níét gepubliceerd is
    assert "GEEN GEPUBLICEERDE MAAT" in tekst
    assert "GEEN GEZAGHEBBENDE BRON" in tekst


def test_markdown_noemt_de_moderne_opvolger(rapportmap):
    """Het rapport mag niet suggereren dat Douma het laatste woord is."""
    tekst = (rapportmap / "rapport.md").read_text(encoding="utf-8")
    assert "LiNT" in tekst
    assert "T-Scan" in tekst


def test_pdf_is_een_pdf(rapportmap):
    assert (rapportmap / "rapport.pdf").read_bytes()[:5] == b"%PDF-"


def _pdf_naar_tekst(pad: Path) -> str:
    import shutil
    import subprocess

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        pytest.skip("pdftotext niet beschikbaar")
    return subprocess.run(
        [pdftotext, str(pad), "-"], capture_output=True, text=True, check=True
    ).stdout


def test_nederlandse_tekens_staan_echt_in_het_rapport(rapportmap):
    """
    Tekens die in dít rapport voorkomen moeten er ook echt in staan.

    Zonder geregistreerd Unicode-lettertype laat reportlab ze zonder
    foutmelding weg.
    """
    uitvoer = _pdf_naar_tekst(rapportmap / "rapport.pdf")
    for teken in ("—", "ë", "ü", "„", "«"):
        assert teken in uitvoer, f"{teken!r} ontbreekt in de PDF"


def test_lettertype_kan_alle_risicotekens_aan(tmp_path):
    """
    Het lettertypemechanisme los getest, met een proeftekst.

    Het rapport bevat toevallig niet elk lastig teken, dus dit is de eigenlijke
    test op de TTF-registratie: alles wat buiten WinAnsi valt en dat een
    Nederlands rapport nodig kan hebben.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    from leesbaarheid.rapport import DEJAVU, _registreer_fonts

    assert _registreer_fonts(), "DejaVuSans kon niet worden geregistreerd"

    proef = (
        "„Zo'n reünie in België,\" zei hij — een naïef café, "
        "coördinatie, «citaat», 'ja', 'één'."
    )
    pad = tmp_path / "proef.pdf"

    doc = SimpleDocTemplate(str(pad), pagesize=A4)
    doc.build([Paragraph(proef, ParagraphStyle("p", fontName=DEJAVU, fontSize=11))])

    uitvoer = _pdf_naar_tekst(pad)
    for teken in ("„", "ë", "ü", "é", "ï", "ö", "—", "«", "»"):
        assert teken in uitvoer, f"{teken!r} viel uit de PDF"


def test_dataframe_kolommen(manuscript):
    df = naar_dataframe(manuscript)
    verwacht = {
        "hoofdstuk", "woorden", "flesch_douma", "leesindex_a", "fog_nl",
        "moeilijk_pct", "passief_pct", "tang_pct", "dialoog_pct",
    }
    assert verwacht <= set(df.columns)
    assert len(df) == 4


def test_scores_zijn_plausibel(manuscript):
    """
    Het bureaucratische hoofdstuk hoort het moeilijkst te zijn.

    Hoofdstuk 2 zit vol lijdende vorm, naamwoordstijl en lange samenstellingen;
    hoofdstuk 3 is korte zinnen en gewone woorden. Meet de tool dat verschil?
    """
    op_naam = {h.hoofdstuk.naam: h for h in manuscript.hoofdstukken}
    ziekenhuis = op_naam["02_het_ziekenhuis"]
    thuis = op_naam["03_thuis"]

    assert ziekenhuis.leesbaarheid.flesch_douma < thuis.leesbaarheid.flesch_douma
    assert ziekenhuis.woordenschat.moeilijk_pct > thuis.woordenschat.moeilijk_pct


def test_samenstellingen_worden_gered(manuscript):
    """ziekenhuisopname, basisschoolleerling, koffiezetapparaat: lang, niet moeilijk."""
    op_naam = {h.hoofdstuk.naam: h for h in manuscript.hoofdstukken}
    assert op_naam["02_het_ziekenhuis"].woordenschat.samenstellingen_gered >= 3


def test_momentopname_en_index(manuscript, tmp_path):
    wortel = tmp_path / "rapporten"
    map_uit = maak_rapport(manuscript, map_uit=None, wortel=wortel)

    gegevens = json.loads((map_uit / "samenvatting.json").read_text(encoding="utf-8"))
    assert gegevens["hoofdstukken"] == 4
    assert gegevens["woorden"] > 300

    index = schrijf_index(wortel)
    assert index is not None
    assert map_uit.name in index.read_text(encoding="utf-8")


def test_index_telt_de_snelkoppeling_niet_mee(manuscript, tmp_path):
    """
    'laatste' wijst naar een van de runs; zonder filter komt die run twee keer
    in het overzicht te staan.
    """
    wortel = tmp_path / "rapporten"
    maak_rapport(manuscript, map_uit=None, wortel=wortel)
    maak_rapport(manuscript, map_uit=None, wortel=wortel)

    regels = [
        r for r in schrijf_index(wortel).read_text(encoding="utf-8").splitlines()
        if r.startswith("| [")
    ]
    assert len(regels) == 2
    assert not any("laatste" in r for r in regels)
