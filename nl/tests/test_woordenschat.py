"""
Woordenschat: de samenstellingscorrectie is hier het punt.

De hele reden om frequentie te gebruiken in plaats van lettergrepen is dat
Nederlandse samenstellingen lang zijn zonder moeilijk te zijn. Deze tests
leggen vast dat dat onderscheid ook echt gemaakt wordt.
"""

import pytest

from leesbaarheid.woordenschat import (
    is_moeilijk,
    mtld,
    splits_samenstelling,
    ttr,
    zipf,
)

# Lange, doorzichtige samenstellingen: zeldzaam als geheel, alledaags in delen.
DOORZICHTIG = [
    "ziekenhuisopname",
    "basisschoolleerling",
    "vergunningsaanvraag",
    "koffiezetapparaat",
]

# Echt moeilijke woorden: laagfrequent én niet te ontleden.
MOEILIJK = [
    "melancholie",
    "obstinaat",
    "pandemonium",
    "onthutst",
]

# Alledaagse woorden.
GEWOON = ["kat", "huis", "lopen", "tafel", "organisatie", "onmiddellijk"]


@pytest.mark.parametrize("woord", DOORZICHTIG)
def test_samenstelling_valt_uiteen(woord):
    delen = splits_samenstelling(woord)
    assert len(delen) > 1, f"{woord} had gesplitst moeten worden, kreeg {delen}"


@pytest.mark.parametrize("woord", DOORZICHTIG)
def test_samenstelling_telt_niet_als_moeilijk(woord):
    assert zipf(woord) < 3.0, "testaanname: dit woord is als geheel zeldzaam"
    assert not is_moeilijk(woord)


@pytest.mark.parametrize("woord", MOEILIJK)
def test_moeilijk_woord_blijft_moeilijk(woord):
    assert is_moeilijk(woord)


@pytest.mark.parametrize("woord", MOEILIJK)
def test_moeilijk_woord_valt_niet_uiteen(woord):
    assert splits_samenstelling(woord) == (woord,)


@pytest.mark.parametrize("woord", GEWOON)
def test_gewoon_woord_is_niet_moeilijk(woord):
    assert not is_moeilijk(woord)


def test_tussenklank_s_wordt_herkend():
    assert splits_samenstelling("vergunningsaanvraag") == ("vergunning", "aanvraag")


def test_meervoudige_splitsing():
    delen = splits_samenstelling("koffiezetapparaat")
    assert len(delen) >= 2
    assert delen[0] == "koffie"


def test_kort_woord_wordt_niet_gesplitst():
    assert splits_samenstelling("kat") == ("kat",)
    assert splits_samenstelling("huisje") == ("huisje",)


def test_ttr():
    assert ttr(["a", "b", "c"]) == pytest.approx(1.0)
    assert ttr(["a", "a", "a"]) == pytest.approx(1 / 3)
    assert ttr([]) == 0.0


def test_mtld_is_hoger_bij_meer_variatie():
    gevarieerd = [f"woord{i}" for i in range(200)]
    eentonig = ["kat", "hond"] * 100
    assert mtld(gevarieerd) > mtld(eentonig)


def test_mtld_is_symmetrisch():
    """
    Twee richtingen gemiddeld: omkeren mag de uitkomst niet veranderen. Dit is
    precies wat de enkelzijdige versie in read_stats.py niet haalt.
    """
    tokens = ["kat", "hond", "muis", "kat", "vogel", "hond", "kat", "vis"] * 8
    assert mtld(tokens) == pytest.approx(mtld(list(reversed(tokens))))


def test_mtld_leeg():
    assert mtld([]) == 0.0
