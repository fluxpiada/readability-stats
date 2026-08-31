"""
Stijlherkenning tegen zinnen waarvan we het antwoord kennen.

Deze tests draaien het echte spaCy-model, dus ze zijn trager dan de rest. Ze
zijn wel het enige dat aantoont dat de dependency-labels doen wat we denken.
"""

import pytest

from leesbaarheid.stijl import (
    TANG_DREMPEL,
    analyseer,
    heeft_agens,
    is_passief,
    naamwoordstijl,
    schrapwoorden_in,
    tangconstructie,
)
from leesbaarheid.taal import ontleed


def eerste_zin(tekst):
    return list(ontleed(tekst).sents)[0]


PASSIEF = [
    "De brief werd door de directeur ondertekend.",
    "Het huis is vorig jaar verkocht.",
    "Er wordt veel gepraat.",
    "De bewoners werden schriftelijk op de hoogte gesteld.",
]

ACTIEF = [
    "De directeur ondertekende de brief.",
    "Zij liep de gang door.",
    "Het huis rook naar oude kranten.",
]


@pytest.mark.parametrize("zin", PASSIEF)
def test_passief_wordt_herkend(zin):
    assert is_passief(eerste_zin(zin))


@pytest.mark.parametrize("zin", ACTIEF)
def test_actief_wordt_niet_als_passief_geteld(zin):
    assert not is_passief(eerste_zin(zin))


def test_agens_wordt_onderscheiden():
    """
    "Door wie?" is het verschil tussen een functionele en een verhullende
    lijdende vorm; daarom melden we het apart.
    """
    assert heeft_agens(eerste_zin("De brief werd door de directeur ondertekend."))
    assert not heeft_agens(eerste_zin("De brief werd ondertekend."))


@pytest.mark.parametrize(
    "zin",
    [
        "De brief werd door de directeur ondertekend.",
        "De brief werd uiteindelijk door zijn zus opengemaakt.",
        "Door de gemeente werd besloten dat de brug gesloten zou blijven.",
    ],
)
def test_agens_ook_zonder_het_fijne_label(zin):
    """
    Het kleine model kent `obl:agent` niet consequent toe: "door de directeur"
    krijgt het wel, "door zijn zus" wordt een gewone `obl`. De detectie mag
    daar niet van afhangen.
    """
    assert heeft_agens(eerste_zin(zin))


def test_geen_agens_bij_ander_voorzetsel():
    """"door" moet er echt staan; "met de hand" is geen handelende persoon."""
    assert not heeft_agens(
        eerste_zin("Het adres was met de hand geschreven.")
    )


def test_min_is_geen_schrapwoord():
    """"min veertien graden" is een temperatuur, geen stoplap."""
    assert schrapwoorden_in(eerste_zin("Het was min veertien graden.")) == []
    assert "min of meer" in schrapwoorden_in(
        eerste_zin("Hij was min of meer tevreden.")
    )


def test_tangconstructie_scheidbaar_werkwoord():
    """Onze Taal noemt dit als eerste geval: de delen van "opbellen" uiteen."""
    zin = eerste_zin(
        "Hij belde zijn moeder na een lange, vermoeiende en rampzalige dag op."
    )
    gevonden = tangconstructie(zin)
    assert gevonden is not None
    afstand, soort = gevonden
    assert afstand > TANG_DREMPEL
    assert "scheidbaar" in soort


def test_korte_zin_is_geen_tangconstructie():
    assert tangconstructie(eerste_zin("Hij belde zijn moeder op.")) is None
    assert tangconstructie(eerste_zin("De kat zat op de mat.")) is None


def test_naamwoordstijl():
    gevonden = naamwoordstijl(eerste_zin("Zij nam een beslissing over de aanvraag."))
    assert gevonden
    assert gevonden[0][0] == "beslissing"


def test_naamwoordstijl_alleen_bij_licht_werkwoord():
    """
    "De beslissing viel zwaar" is gewoon een zin met een naamwoord erin; daar
    valt niets te vereenvoudigen, dus die moet niet meetellen.
    """
    assert not naamwoordstijl(eerste_zin("De beslissing viel haar zwaar."))


def test_schrapwoorden():
    gevonden = schrapwoorden_in(
        eerste_zin("Dat was eigenlijk gewoon typisch, natuurlijk.")
    )
    assert set(gevonden) >= {"eigenlijk", "gewoon", "natuurlijk"}


def test_schrapuitdrukking_van_meerdere_woorden():
    gevonden = schrapwoorden_in(eerste_zin("Het was in feite een goed idee."))
    assert "in feite" in gevonden


def test_schone_zin_levert_niets_op():
    assert schrapwoorden_in(eerste_zin("De trap kraakte.")) == []


def test_analyseer_geeft_samenhangende_cijfers():
    tekst = (
        "De brief werd door de directeur ondertekend. "
        "Zij nam een beslissing over de aanvraag. "
        "Dat was eigenlijk gewoon typisch. "
        "De trap kraakte."
    )
    uitkomst = analyseer(ontleed(tekst))

    assert uitkomst.zinnen == 4
    assert uitkomst.passief_zinnen == 1
    assert uitkomst.passief_pct == pytest.approx(25.0)
    assert uitkomst.naamwoordstijl >= 1
    assert uitkomst.schrapwoorden >= 2
    assert uitkomst.voorbeelden["passief"], "voorbeelden horen erbij te zitten"


def test_percentages_blijven_binnen_bereik():
    uitkomst = analyseer(ontleed("De trap kraakte. Het huis rook naar kranten."))
    assert 0 <= uitkomst.passief_pct <= 100
    assert 0 <= uitkomst.tang_pct <= 100
