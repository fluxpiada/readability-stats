"""
De gouden tabel voor de lettergreepteller.

Alles in deze tool — Flesch-Douma, Leesindex A, het percentage lange woorden —
staat of valt met deze getallen. Ze zijn met de hand gecontroleerd op
fonologische lettergrepen (hoe je het woord uitspreekt), niet op afbreekpunten.
"""

import pytest

from leesbaarheid.lettergrepen import (
    _pyphen,
    tel_kernen,
    tel_lettergrepen,
    tel_lettergrepen_zonder_pyphen,
)

# woord -> aantal lettergrepen bij normale uitspraak
GOUDEN_TABEL = {
    # eenlettergrepig, inclusief de tweeklanken waar de Engelse teller op stukloopt
    "paard": 1,
    "ijs": 1,
    "huis": 1,
    "vrouw": 1,
    "oog": 1,
    "strand": 1,
    "de": 1,
    "het": 1,
    "ik": 1,
    "een": 1,
    "nieuw": 1,
    # slot-e is in het Nederlands een uitgesproken sjwa, geen "silent e"
    "hoge": 2,
    "lopen": 2,
    "water": 2,
    "boeken": 2,
    "meisje": 2,
    # tweeklanken en drieklanken als één kern
    "mooie": 2,
    "koeien": 2,
    "eeuwig": 2,
    "schreeuwen": 2,
    "auto": 2,
    "aaien": 2,
    # trema: breekt de klinkergroep juist open
    "zeeën": 2,
    "reünie": 3,
    "België": 3,
    "naïef": 2,
    "poëzie": 3,
    "coördinatie": 5,
    "zeeëngte": 3,
    # accenten zonder trema horen bij de kern
    "één": 1,
    "café": 2,
    # meerlettergrepig
    "bijzonder": 3,
    "aardappel": 3,
    "onmiddellijk": 4,
    "televisie": 4,
    "organisatie": 5,
    "gebeurtenis": 4,
    "waarschijnlijk": 3,
    "nauwelijks": 3,
    "tussenin": 3,
    "provincie": 3,
    "familie": 3,
    "chaos": 2,
    "theater": 3,
    "idee": 2,
    "museum": 3,
    # samenstellingen: het geval waarvoor "3+ lettergrepen = moeilijk" onbruikbaar is
    "ziekenhuisopname": 6,
    "basisschoolleerling": 5,
}

# Woorden waar de terugval (kernen tellen zonder woordenboek) het mis heeft.
# Zonder lettergreepgrenzen ziet hij niet dat een klinkerpaar over een grens
# loopt en dus geen tweeklank is. Vastgelegd zodat de afwijking zichtbaar
# blijft in plaats van stilletjes te groeien.
TERUGVAL_AFWIJKINGEN = {
    "museum": 2,        # "mu-se-um": de "eu" loopt over een grens, geen tweeklank
}


@pytest.mark.parametrize("woord, verwacht", sorted(GOUDEN_TABEL.items()))
def test_gouden_tabel(woord, verwacht):
    assert tel_lettergrepen(woord) == verwacht


@pytest.mark.parametrize("woord, verwacht", sorted(GOUDEN_TABEL.items()))
def test_terugval_zonder_pyphen(woord, verwacht):
    """
    De terugval moet de gouden tabel halen, op de vastgelegde uitzonderingen na.
    """
    verwacht = TERUGVAL_AFWIJKINGEN.get(woord, verwacht)
    assert tel_lettergrepen_zonder_pyphen(woord) == verwacht


def test_pyphen_is_geinstalleerd():
    """
    Niet strikt nodig om te draaien, maar wel de bedoelde opstelling: zonder
    pyphen zijn de cijfers meetbaar minder nauwkeurig.
    """
    assert _pyphen() is not None, "pyphen ontbreekt — draai: uv sync --group nl"


def test_hoofdletters_en_leestekens_doen_niet_mee():
    assert tel_lettergrepen("België") == tel_lettergrepen("belgië")
    assert tel_lettergrepen("'s") == 1
    assert tel_lettergrepen("kant-en-klaar") == tel_lettergrepen("kantenklaar")


def test_lege_invoer():
    assert tel_lettergrepen("") == 0
    assert tel_lettergrepen("—") == 0
    assert tel_lettergrepen("123") == 0


def test_woord_met_letters_telt_altijd_minstens_een():
    assert tel_lettergrepen("zw") == 1      # geen klinker, maar wel een woord


def test_kernenteller_los():
    assert tel_kernen("ooi") == 1
    assert tel_kernen("ooie") == 2
    assert tel_kernen("") == 0
    assert tel_kernen("str") == 0
