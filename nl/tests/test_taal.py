"""
Modelkeuze — zonder iets te downloaden.

De grote modellen staan hier niet geïnstalleerd, dus deze tests gaan over de
keuzelogica, nooit over het daadwerkelijk laden.
"""

import re
from pathlib import Path

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
def test_elk_model_heeft_een_eigen_groep(sleutel):
    """
    De wheel-URL's staan in pyproject.toml onder [tool.uv.sources], zodat de
    modellen in uv.lock staan en `uv sync` ze niet weggooit. Elk model wijst
    dus naar de dependency-groep die het levert.
    """
    groep = taal.MODELLEN[sleutel].groep
    assert groep in ("nl", "nl-md", "nl-lg")

    wortel = Path(__file__).resolve().parents[2]
    pyproject = (wortel / "pyproject.toml").read_text(encoding="utf-8")
    assert f"{groep} = [" in pyproject, f"groep {groep} ontbreekt in pyproject.toml"
    assert taal.MODELLEN[sleutel].naam.replace("_", "-") in pyproject


def test_wheelurls_hebben_dezelfde_versie():
    """Een losse versie zou betekenen dat de modellen onderling niet matchen."""
    wortel = Path(__file__).resolve().parents[2]
    pyproject = (wortel / "pyproject.toml").read_text(encoding="utf-8")
    versies = set(re.findall(r"nl_core_news_(?:sm|md|lg)-(\d+\.\d+\.\d+)-py3", pyproject))
    assert len(versies) == 1, f"modellen staan op verschillende versies: {versies}"


def test_korte_en_volledige_naam_werken_allebei():
    assert taal.volledige_naam("md") == "nl_core_news_md"
    assert taal.volledige_naam("nl_core_news_md") == "nl_core_news_md"


def test_volledige_naam_wijst_onbekende_namen_af():
    """Eén controle voor elke manier om een model te kiezen."""
    with pytest.raises(ValueError):
        taal.volledige_naam("nl_core_news_xl")


def test_standaardmodel_is_geinstalleerd():
    assert taal.beschikbare_modellen()["sm"] is True


def test_onbekend_model_wordt_afgewezen():
    with pytest.raises(ValueError) as fout:
        taal.kies_model("xl")
    # de melding moet vertellen wat er dan wél kan
    assert "sm" in str(fout.value) and "md" in str(fout.value)


def test_installatieopdracht_synct_een_groep():
    """
    Niet `uv pip install <wheel>`: wat daarmee binnenkomt staat niet in uv.lock,
    dus de versie ligt niet vast. En niet `python -m spacy download`: dat roept
    pip aan, en een door uv beheerde omgeving heeft geen pip.
    """
    opdracht = taal.installatieopdracht("md")
    assert opdracht == "uv sync --inexact --group nl --group nl-md"
    assert "spacy download" not in opdracht
    assert "uv pip install" not in opdracht


def test_installeren_gooit_een_ander_model_niet_weg():
    """
    Een groep-sync maakt de omgeving precies gelijk aan de genoemde groepen.
    Zonder --inexact zou het ophalen van md het al aanwezige lg verwijderen —
    precies de fout die deze opzet moet voorkomen.
    """
    assert "--inexact" in taal.installatieopdracht("md")


def test_voorrang_env_boven_voorkeur(monkeypatch, tmp_path):
    monkeypatch.setattr(taal, "_sessiemodel", None)
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", tmp_path / ".taalmodel")
    (tmp_path / ".taalmodel").write_text("nl_core_news_lg\n", encoding="utf-8")

    monkeypatch.setenv("RS_SPACY_MODEL", "nl_core_news_md")
    assert taal.huidig_model() == "nl_core_news_md"

    monkeypatch.delenv("RS_SPACY_MODEL")
    assert taal.huidig_model() == "nl_core_news_lg"


def test_keuze_voor_deze_run_gaat_boven_alles(monkeypatch, tmp_path):
    """
    `--model` moet echt voorrang hebben, niet toevallig werken doordat het
    model al geladen is.
    """
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", tmp_path / ".taalmodel")
    (tmp_path / ".taalmodel").write_text("nl_core_news_lg\n", encoding="utf-8")
    monkeypatch.setenv("RS_SPACY_MODEL", "nl_core_news_sm")
    monkeypatch.setattr(taal, "_sessiemodel", None)

    assert taal.stel_model_in("md") == "nl_core_news_md"
    assert taal.huidig_model() == "nl_core_news_md"


def test_zonder_voorkeur_het_standaardmodel(monkeypatch, tmp_path):
    monkeypatch.setattr(taal, "_sessiemodel", None)
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", tmp_path / "bestaat-niet")
    monkeypatch.delenv("RS_SPACY_MODEL", raising=False)
    assert taal.huidig_model() == taal.STANDAARDMODEL


def test_kies_model_schrijft_de_voorkeur(monkeypatch, tmp_path):
    bestand = tmp_path / ".taalmodel"
    monkeypatch.setattr(taal, "_sessiemodel", None)
    monkeypatch.setattr(taal, "VOORKEURSBESTAND", bestand)
    monkeypatch.delenv("RS_SPACY_MODEL", raising=False)

    assert taal.kies_model("md") == "nl_core_news_md"
    assert bestand.read_text(encoding="utf-8").strip() == "nl_core_news_md"
    assert taal.huidig_model() == "nl_core_news_md"

    taal.kies_model("sm")          # terugzetten voor de rest van de tests
