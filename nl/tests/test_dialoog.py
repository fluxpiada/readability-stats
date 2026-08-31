"""
Dialoogherkenning, conventiedetectie en zinsritme.

Het uitgangspunt: er is geen officiële Nederlandse dialoogregel, dus de tool
mag er geen opleggen. Hij moet vaststellen wat het manuscript zelf doet.
"""

import pytest

from leesbaarheid.dialoog import (
    analyseer_dialoog,
    analyseer_tempo,
    dominante_conventie,
    is_dialoogalinea,
    tel_conventies,
    zinslengtes,
)
from leesbaarheid.taal import ontleed


def test_enkele_aanhalingstekens():
    assert dominante_conventie("'Kom binnen,' zei hij.") == "enkele aanhalingstekens"


def test_lage_aanhalingstekens():
    assert dominante_conventie("„Kom binnen,” zei hij.") == "lage aanhalingstekens"


def test_dialoogstreepje():
    assert dominante_conventie("— Kom binnen, zei hij.") == "dialoogstreepje"


def test_dominante_conventie_wint():
    """
    Een manuscript dat overwegend enkele aanhalingstekens gebruikt met één
    uitschieter, hanteert de enkele conventie.
    """
    tekst = "\n\n".join(["'Ja,' zei ze."] * 5 + ['"Nee," zei hij.'])
    assert dominante_conventie(tekst) == "enkele aanhalingstekens"


def test_gemengd_gebruik_is_zichtbaar():
    """Voor de consistentiecontrole moeten álle gevonden soorten terugkomen."""
    tekst = "'Ja,' zei ze.\n\n„Nee,” zei hij."
    gevonden = tel_conventies(tekst)
    assert len(gevonden) >= 2


def test_vertellende_tekst_heeft_geen_conventie():
    assert dominante_conventie("Het huis rook naar oude kranten. De trap kraakte.") is None


def test_dialoogalinea_herkennen():
    assert is_dialoogalinea("'Kom binnen,' zei hij.")
    assert is_dialoogalinea("— Kom binnen.")
    assert not is_dialoogalinea("Hij liep de kamer in en deed de deur dicht.")


def test_dialoogaandeel():
    tekst = (
        "Hij liep de kamer binnen en keek om zich heen naar de lege stoelen.\n\n"
        "'Is daar iemand?'\n\n"
        "Niemand gaf antwoord."
    )
    uitkomst = analyseer_dialoog(tekst)
    assert uitkomst.alineas == 3
    assert uitkomst.dialoogalineas == 1
    assert 0 < uitkomst.dialoog_pct < 50


def test_tekst_zonder_dialoog():
    uitkomst = analyseer_dialoog("Het huis rook naar oude kranten.")
    assert uitkomst.dialoogalineas == 0
    assert uitkomst.dialoog_pct == 0.0


def test_afwijkend_hoofdstuk_wordt_herkend():
    """
    Een hoofdstuk met lage aanhalingstekens in een boek vol enkele
    aanhalingstekens moet opvallen — dat is de consistentiecontrole.
    """
    hoofdstuk = "„Dit is anders,\" zei hij.\n\n„En dit ook,\" zei zij."
    uitkomst = analyseer_dialoog(hoofdstuk, manuscript_conventie="enkele aanhalingstekens")

    assert uitkomst.conventie == "lage aanhalingstekens"
    assert uitkomst.wijkt_af


def test_hoofdstuk_dat_de_conventie_volgt_wijkt_niet_af():
    uitkomst = analyseer_dialoog(
        "'Dit klopt,' zei hij.", manuscript_conventie="enkele aanhalingstekens"
    )
    assert not uitkomst.wijkt_af


def test_afwijkend_hoofdstuk_telt_nog_steeds_als_dialoog():
    """
    De valkuil: als we alleen op de manuscriptconventie zouden zoeken, telt juist
    het afwijkende hoofdstuk als 'geen dialoog' — en dat is het hoofdstuk dat we
    willen vinden.
    """
    uitkomst = analyseer_dialoog(
        "„Kom binnen,\" zei hij.", manuscript_conventie="enkele aanhalingstekens"
    )
    assert uitkomst.dialoogalineas == 1
    assert uitkomst.dialoog_pct > 0


def test_zinslengtes():
    doc = ontleed("Hij liep. Zij bleef staan bij de deur van de keuken.")
    lengtes = zinslengtes(doc)
    assert lengtes[0] == 2
    assert lengtes[1] > lengtes[0]


def test_tempo_spreiding_onderscheidt_ritme():
    """
    De spreiding is de eigenlijke tempomaat: even lange zinnen lezen vlak,
    ook als het gemiddelde gelijk is.
    """
    vlak = ontleed(" ".join(["De man liep naar huis."] * 8))
    afwisselend = ontleed(
        "Hij stopte. "
        "De man liep langzaam door de lange, stille straat naar het huis van zijn moeder. "
        "Toen niets. "
        "Zij wachtte al uren bij het raam en keek naar de regen die tegen het glas sloeg."
    )
    assert analyseer_tempo(afwisselend).spreiding > analyseer_tempo(vlak).spreiding


def test_tempo_op_lege_tekst():
    uitkomst = analyseer_tempo(ontleed(""))
    assert uitkomst.zinnen == 0
    assert uitkomst.gemiddelde == 0.0


def test_tempo_cijfers_kloppen_onderling():
    uitkomst = analyseer_tempo(ontleed("Hij liep. Zij wachtte bij de deur van de keuken."))
    assert uitkomst.zinnen == len(uitkomst.lengtes)
    assert min(uitkomst.lengtes) <= uitkomst.mediaan <= max(uitkomst.lengtes)
    assert uitkomst.p90 <= max(uitkomst.lengtes)
