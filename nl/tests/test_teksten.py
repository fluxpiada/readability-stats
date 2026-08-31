"""
De bereik- en streefzonetabel.

Deze tests bewaken twee dingen die makkelijk stilletjes misgaan: een kolom die
wordt toegevoegd zonder bereikinformatie, en een maat die een streefzone krijgt
terwijl er geen betere kant bestaat.
"""

import pytest

from leesbaarheid import rapport, teksten


def test_elke_maat_heeft_bereikinformatie():
    """
    Elke maat in de begrippenlijst moet een bereikregel kunnen opleveren.

    'conventie' is de uitzondering: consistentie van aanhalingstekens is geen
    getal en heeft dus geen bereik.
    """
    zonder = [
        m.naam for m in teksten.MATEN
        if m.sleutel != "conventie" and not teksten.bereik_regel(m.sleutel)
    ]
    assert not zonder, f"geen bereik gevonden voor: {zonder}"


@pytest.mark.parametrize("sleutel, bereik", sorted(teksten.BEREIKEN.items()))
def test_bereik_is_volledig_ingevuld(sleutel, bereik):
    assert bereik.bereik.strip()
    assert bereik.richting in teksten.RICHTINGEN
    assert bereik.streefzone.strip()
    # vrije tekst, maar wel classificeerbaar: er moet uit blijken of de zone
    # uit de literatuur komt of van ons
    assert any(bron in bereik.streefbron for bron in teksten.STREEFBRONNEN), (
        f"streefbron '{bereik.streefbron}' noemt geen bekende herkomst"
    )


@pytest.mark.parametrize("sleutel, bereik", sorted(teksten.BEREIKEN.items()))
def test_geen_richting_betekent_geen_streefwaarde(sleutel, bereik):
    """
    Een maat zonder betere kant mag geen streefzone krijgen.

    Dialoogaandeel is genreafhankelijk; daar een bereik op plakken zou doen
    alsof er een goed antwoord is.
    """
    if bereik.richting == "geen":
        assert not bereik.heeft_streefzone, (
            f"{sleutel} heeft geen richting maar wél een streefzone"
        )


def test_elke_tabelkolom_heeft_een_bereik():
    """Vangt: iemand voegt een kolom toe en vergeet de bereikinformatie."""
    for tabel, sleutels in rapport.TABELKOLOMMEN.items():
        for sleutel in sleutels:
            assert sleutel in teksten.BEREIKEN, (
                f"kolom '{sleutel}' in tabel '{tabel}' heeft geen bereik"
            )


def test_elke_tabel_heeft_een_legenda():
    for tabel in rapport.TABELKOLOMMEN:
        assert rapport.legenda_voor(tabel).strip()


def test_legenda_legt_elk_gebruikt_symbool_uit():
    """Een kop mag nooit een symbool tonen dat de legenda niet noemt."""
    for tabel, sleutels in rapport.TABELKOLOMMEN.items():
        uitleg = rapport.legenda_voor(tabel)
        for sleutel in sleutels:
            symbool = teksten.BEREIKEN[sleutel].symbool
            assert symbool in uitleg, (
                f"symbool {symbool} van '{sleutel}' ontbreekt in legenda van '{tabel}'"
            )


def test_kop_krijgt_symbool():
    assert teksten.kop("flesch_douma", "Flesch-Douma") == "Flesch-Douma ↑"
    assert teksten.kop("fog_nl", "Fog-NL") == "Fog-NL ↓"
    assert teksten.kop("dialoog_pct", "Dialoog %") == "Dialoog % •"


def test_kop_zonder_bereik_blijft_ongewijzigd():
    assert teksten.kop("hoofdstuk", "Hoofdstuk") == "Hoofdstuk"


def test_legenda_van_onbekende_kolommen_is_leeg():
    assert teksten.legenda(["hoofdstuk", "woorden"]) == ""


def test_bereikregel_noemt_de_herkomst_van_de_zone():
    """
    Waar de streefzone van ons is, moet dat er staan — anders lijkt onze
    inschatting net zo hard als een gepubliceerde band.
    """
    regel = teksten.bereik_regel("mtld")
    assert "60–120" in regel
    assert "eigen richtlijn" in regel


def test_bereikregel_zonder_streefzone_belooft_niets():
    regel = teksten.bereik_regel("dialoog_pct")
    assert "genreafhankelijk" in regel
    assert "Streefzone" not in regel
