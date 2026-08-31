"""
De formules tegen handberekeningen.

Het doel is niet "de code doet wat de code doet", maar: staan de gepubliceerde
constanten er nog in, en rekenen we ermee zoals Douma en Brouwer het bedoeld
hebben. Daarom zijn de verwachte waarden hier met de hand uitgerekend uit de
formule, niet uit een eerdere run overgenomen.
"""

import pytest

from leesbaarheid import formules
from leesbaarheid.formules import bereken, flesch_douma, leesindex_a


def test_douma_handberekening():
    # 100 woorden, 5 zinnen, 150 lettergrepen
    #   206.84 − 0.77 × 150 − 0.93 × 20
    #   = 206.84 − 115.5 − 18.6 = 72.74
    assert flesch_douma(100, 5, 150) == pytest.approx(72.74)


def test_leesindex_a_handberekening():
    # 100 woorden, 5 zinnen, 150 lettergrepen
    #   195 − 67 × 1.5 − 2 × 20
    #   = 195 − 100.5 − 40 = 54.5
    assert leesindex_a(100, 5, 150) == pytest.approx(54.5)


def test_constanten_zijn_die_van_de_publicaties():
    """Deze getallen zijn de bron. Wijzigen betekent: een andere formule."""
    assert formules.DOUMA_BASIS == 206.84
    assert formules.DOUMA_WOORDLENGTE == 0.77
    assert formules.DOUMA_ZINSLENGTE == 0.93
    assert formules.BROUWER_BASIS == 195.0
    assert formules.BROUWER_WOORDLENGTE == 67.0
    assert formules.BROUWER_ZINSLENGTE == 2.0


def test_kortere_zinnen_geven_een_hogere_score():
    lang = flesch_douma(woorden=100, zinnen=4, lettergrepen=150)
    kort = flesch_douma(woorden=100, zinnen=10, lettergrepen=150)
    assert kort > lang


def test_langere_woorden_geven_een_lagere_score():
    makkelijk = flesch_douma(woorden=100, zinnen=5, lettergrepen=120)
    moeilijk = flesch_douma(woorden=100, zinnen=5, lettergrepen=200)
    assert moeilijk < makkelijk


def test_bereken_op_een_echte_zin():
    # "De kat zat op de mat." -> 6 woorden, 1 zin, elk woord 1 lettergreep
    woorden = ["De", "kat", "zat", "op", "de", "mat"]
    uitkomst = bereken(woorden, aantal_zinnen=1)

    assert uitkomst.woorden == 6
    assert uitkomst.lettergrepen == 6
    assert uitkomst.woorden_per_zin == pytest.approx(6.0)
    assert uitkomst.lettergrepen_per_woord == pytest.approx(1.0)
    # 206.84 − 0.77 × 100 − 0.93 × 6 = 206.84 − 77 − 5.58 = 124.26
    assert uitkomst.flesch_douma == pytest.approx(124.26)
    assert uitkomst.fog_nl is None          # zonder moeilijkwoordtelling


def test_lege_tekst_geeft_niets():
    assert bereken([], 0) is None
    assert bereken(["woord"], 0) is None


def test_lange_woorden_percentage():
    woorden = ["ziekenhuisopname", "kat", "organisatie", "de"]
    uitkomst = bereken(woorden, aantal_zinnen=1)
    # ziekenhuisopname (6) en organisatie (5) hebben >= 4 lettergrepen
    assert uitkomst.lange_woorden_pct == pytest.approx(50.0)
    # > 9 letters: ziekenhuisopname (16), organisatie (11)
    assert uitkomst.lange_letters_pct == pytest.approx(50.0)


def test_fog_nl_gebruikt_de_meegegeven_moeilijkheid():
    woorden = ["woord"] * 100
    uitkomst = bereken(woorden, aantal_zinnen=10, moeilijke_woorden=5)
    # 0.4 × (10 + 100 × 0.05) = 0.4 × 15 = 6.0
    assert uitkomst.fog_nl == pytest.approx(6.0)
    assert uitkomst.moeilijke_woorden_pct == pytest.approx(5.0)


@pytest.mark.parametrize(
    "score, verwacht",
    [(95, "zeer makkelijk"), (65, "standaard"), (40, "moeilijk"), (10, "zeer moeilijk")],
)
def test_banden(score, verwacht):
    omschrijving, _ = formules.band(score)
    assert omschrijving == verwacht
