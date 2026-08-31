"""Inlezen, normaliseren en opdelen van manuscriptbestanden."""

from pathlib import Path

import pytest

from leesbaarheid.tekst import (
    laad_hoofdstukken,
    lees_bestand,
    normaliseer,
    splits_hoofdstukken,
    strip_markdown,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_krulapostrof_wordt_recht():
    """
    De fout uit de Engelse versie: "z'n" met krulapostrof viel in twee tokens
    uiteen, zichtbaar in converted_txt/.
    """
    assert normaliseer("z’n boek") == "z'n boek"
    assert "’" not in normaliseer("dat ’s avonds")


def test_aanhalingstekens_blijven_staan():
    """dialoog.py heeft ze nodig om de conventie te bepalen."""
    for teken in ("„", "”", "“", "«", "»"):
        assert teken in normaliseer(f"Hij zei {teken}hallo{teken}")


def test_dialoogstreepje_overleeft_markdown():
    """
    Een streepje aan het regelbegin is in proza vaker dialoog dan opsomming.
    De Engelse stripper haalt het weg; wij niet.
    """
    tekst = strip_markdown("— Kom binnen, zei hij.\n- Ook goed.")
    assert tekst.startswith("—")
    assert "- Ook goed." in tekst


def test_markdown_wordt_gestript():
    tekst = strip_markdown("Dit is **vet** en *schuin* met `code` en [link](http://x)")
    assert "**" not in tekst and "*" not in tekst
    assert "`" not in tekst
    assert "link" in tekst and "http" not in tekst


def test_koppen_blijven_herkenbaar():
    """De kopregel moet blijven staan, anders kan er niet op gesplitst worden."""
    assert "# Hoofdstuk 1" in strip_markdown("# Hoofdstuk 1")


def test_splitsen_op_hoofdstukken():
    tekst = "Hoofdstuk 1\nEerste stuk.\n\nHoofdstuk 2\nTweede stuk."
    stukken = splits_hoofdstukken(tekst)
    assert len(stukken) == 2
    assert "Eerste stuk." in stukken[0][1]
    assert "Tweede stuk." in stukken[1][1]


def test_een_enkele_kop_splitst_niet():
    """Eén kop is de titel van het bestand, niet een hoofdstukgrens."""
    stukken = splits_hoofdstukken("# Hoofdstuk 1\nAlleen dit.")
    assert len(stukken) == 1


def test_proloog_en_epiloog_tellen_mee():
    tekst = "Proloog\nHet begin.\n\nEpiloog\nHet einde."
    assert len(splits_hoofdstukken(tekst)) == 2


def test_docx_met_nederlandse_kopstijl():
    """
    De kern van de docx-ondersteuning: een Nederlandse Word-installatie noemt
    kopstijlen "Kop 1". Herkennen we die als kop?
    """
    tekst = lees_bestand(FIXTURES / "04_het_dorp.docx")
    assert "# Hoofdstuk 4" in tekst


def test_docx_neemt_tabellen_mee():
    """read_stats.py leest alleen doc.paragraphs en verliest tabelinhoud."""
    tekst = lees_bestand(FIXTURES / "04_het_dorp.docx")
    assert "Temperatuur" in tekst
    assert "min veertien graden" in tekst


def test_fixtures_laden():
    hoofdstukken = laad_hoofdstukken(FIXTURES)
    assert len(hoofdstukken) == 4
    assert [h.volgorde for h in hoofdstukken] == [1, 2, 3, 4]
    assert all(h.tekst.strip() for h in hoofdstukken)


def test_volgorde_volgt_bestandsnaam():
    namen = [h.naam for h in laad_hoofdstukken(FIXTURES)]
    assert "1" in namen[0] and "brief" in namen[0].lower()
    assert "4" in namen[3] or "dorp" in namen[3].lower()


def test_lege_map(tmp_path):
    assert laad_hoofdstukken(tmp_path) == []


def test_draft_map_wordt_overgeslagen(tmp_path):
    (tmp_path / "klad").mkdir()
    (tmp_path / "klad" / "oud.md").write_text("Niet meetellen.", encoding="utf-8")
    (tmp_path / "goed.md").write_text("Wel meetellen.", encoding="utf-8")

    hoofdstukken = laad_hoofdstukken(tmp_path)
    assert len(hoofdstukken) == 1
    assert "Wel" in hoofdstukken[0].tekst
