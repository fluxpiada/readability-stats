"""
Modelkeuze — zonder iets te downloaden.

De grote modellen staan hier niet geïnstalleerd, dus deze tests gaan over de
keuzelogica, nooit over het daadwerkelijk laden.
"""

import pytest

from leesbaarheid import taal


def test_de_drie_nederlandse_modellen():
    """
    Voor het Nederlands bestaan alleen sm, md en lg. Er is geen trf-model,
    anders dan voor sommige andere talen — dat is waarom de lijst hier eindigt.
    """
    assert set(taal.MODELLEN) == {"sm", "md", "lg"}
    assert all(m.naam.startswith("nl_core_news_") for m in taal.MODELLEN.values())


@pytest.mark.parametrize("sleutel", ["sm", "md", "lg"])
def test_wheelurl_is_gepind(sleutel):
    """Een losse versie zou betekenen dat runs niet reproduceerbaar zijn."""
    wheel = taal.MODELLEN[sleutel].wheel
    assert wheel.startswith("https://github.com/explosion/spacy-models/releases/")
    assert taal.MODELVERSIE in wheel
    assert wheel.endswith(".whl")


def test_korte_en_volledige_naam_werken_allebei():
    assert taal._volledige_naam("md") == "nl_core_news_md"
    assert taal._volledige_naam("nl_core_news_md") == "nl_core_news_md"


def test_standaardmodel_is_geinstalleerd():
    assert taal.beschikbare_modellen()["sm"] is True


def test_onbekend_model_wordt_afgewezen():
    with pytest.raises(ValueError) as fout:
        taal.kies_model("xl")
    # de melding moet vertellen wat er dan wél kan
    assert "sm" in str(fout.value) and "md" in str(fout.value)


def test_installatieopdracht_gebruikt_uv_pip():
    """
    Niet `python -m spacy download`: dat roept pip aan, en een door uv beheerde
    omgeving heeft geen pip. Dan krijg je een verwarrende fout.
    """
    opdracht = taal.installatieopdracht("md")
    assert opdracht.startswith("uv pip install ")
    assert "nl_core_news_md" in opdracht
    assert "spacy download" not in opdracht


def test_voorrang_env_boven_voorkeur(monkeypatch, tmp_path):
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", tmp_path / ".taalmodel")
    (tmp_path / ".taalmodel").write_text("nl_core_news_lg\n", encoding="utf-8")

    monkeypatch.setenv("RS_SPACY_MODEL", "nl_core_news_md")
    assert taal.huidig_model() == "nl_core_news_md"

    monkeypatch.delenv("RS_SPACY_MODEL")
    assert taal.huidig_model() == "nl_core_news_lg"


def test_zonder_voorkeur_het_standaardmodel(monkeypatch, tmp_path):
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", tmp_path / "bestaat-niet")
    monkeypatch.delenv("RS_SPACY_MODEL", raising=False)
    assert taal.huidig_model() == taal.STANDAARDMODEL


def test_kies_model_schrijft_de_voorkeur(monkeypatch, tmp_path):
    bestand = tmp_path / ".taalmodel"
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", bestand)
    monkeypatch.delenv("RS_SPACY_MODEL", raising=False)

    assert taal.kies_model("md") == "nl_core_news_md"
    assert bestand.read_text(encoding="utf-8").strip() == "nl_core_news_md"
    assert taal.huidig_model() == "nl_core_news_md"

    taal.kies_model("sm")          # terugzetten voor de rest van de tests
