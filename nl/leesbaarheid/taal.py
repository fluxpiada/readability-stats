"""
taal.py — de spaCy-pijplijn, één keer opgezet en gedeeld.

Model: `nl_core_news_sm`, getraind op UD Dutch Alpino en LassySmall (POS-tags en
dependencies), CC BY-SA 4.0. Alpino en Lassy zijn de standaard Nederlandse
syntactische treebanks; daardoor gebruikt het model Universal
Dependencies-labels, en zijn `aux:pass`, `nsubj:pass`, `compound:prt` en
`obl:agent` beschikbaar. Dat is wat passief- en tangconstructiedetectie zonder
regex mogelijk maakt.

Via de omgevingsvariabele `RS_SPACY_MODEL` kun je een groter model kiezen
(`nl_core_news_md`, `nl_core_news_lg`) als de nauwkeurigheid van het kleine
model tekortschiet.

Zinssegmentatie is het zwakke punt van elke Nederlandse pijplijn: afkortingen
als "bijv." en "d.w.z." eindigen op een punt en worden anders als zinseinde
gelezen. De lijst hieronder wordt als tokenizer-uitzondering geregistreerd,
zodat zulke afkortingen één token blijven.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path

_nlp = None
_geladen_model: str | None = None

STANDAARDMODEL = "nl_core_news_sm"

# De modelversie moet met de spaCy-minor meebewegen; staat ook zo in pyproject.toml.
MODELVERSIE = "3.8.0"


@dataclass(frozen=True)
class Model:
    naam: str
    grootte: str
    omschrijving: str

    @property
    def wheel(self) -> str:
        return (
            "https://github.com/explosion/spacy-models/releases/download/"
            f"{self.naam}-{MODELVERSIE}/{self.naam}-{MODELVERSIE}-py3-none-any.whl"
        )


# Voor het Nederlands bestaan alleen deze drie. Er is géén nl_core_news_trf:
# spaCy levert voor het Nederlands geen transformermodel, anders dan voor
# bijvoorbeeld Catalaans of Deens. Dit is dus het hele scala.
MODELLEN: dict[str, Model] = {
    "sm": Model("nl_core_news_sm", "12 MB", "klein en snel; de standaard"),
    "md": Model("nl_core_news_md", "40 MB", "met woordvectoren; de zinnige stap omhoog"),
    "lg": Model("nl_core_news_lg", "541 MB", "grote vectoren; forse download, beperkte winst"),
}

MODEL_PER_NAAM = {m.naam: sleutel for sleutel, m in MODELLEN.items()}

# Onthoudt de keuze tussen sessies. Staat in .gitignore.
VOORKEURSBESTAND = Path(__file__).resolve().parents[1] / ".taalmodel"


def _volledige_naam(keuze: str) -> str:
    """Accepteer zowel 'md' als 'nl_core_news_md'."""
    if keuze in MODELLEN:
        return MODELLEN[keuze].naam
    return keuze


def is_geinstalleerd(naam: str) -> bool:
    """Staat dit model in de omgeving?"""
    try:
        return importlib.util.find_spec(naam) is not None
    except (ImportError, ValueError):
        return False


def beschikbare_modellen() -> dict[str, bool]:
    """Per model of het geïnstalleerd is."""
    return {sleutel: is_geinstalleerd(m.naam) for sleutel, m in MODELLEN.items()}


def _opgeslagen_voorkeur() -> str | None:
    try:
        keuze = VOORKEURSBESTAND.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return _volledige_naam(keuze) if keuze else None


def huidig_model() -> str:
    """
    Welk model draait er, in volgorde van voorrang:
    expliciete keuze → RS_SPACY_MODEL → opgeslagen voorkeur → standaard.
    """
    return (
        os.environ.get("RS_SPACY_MODEL")
        or _opgeslagen_voorkeur()
        or STANDAARDMODEL
    )


def kies_model(keuze: str) -> str:
    """
    Leg *keuze* vast als voorkeur voor volgende runs.

    Controleert de naam, maar niet of het model al geïnstalleerd is: het mag
    ingesteld worden vlak voordat het wordt opgehaald.
    """
    naam = _volledige_naam(keuze)
    if naam not in MODEL_PER_NAAM:
        bekend = ", ".join(f"{s} ({m.naam})" for s, m in MODELLEN.items())
        raise ValueError(f"Onbekend model: {keuze}. Kies uit: {bekend}")

    VOORKEURSBESTAND.write_text(naam + "\n", encoding="utf-8")
    global _nlp, _geladen_model
    if _geladen_model and _geladen_model != naam:
        _nlp, _geladen_model = None, None      # bij de volgende aanroep opnieuw laden
    return naam


def installatieopdracht(keuze: str) -> str:
    """
    De opdracht die dit model ophaalt.

    Bewust `uv pip install` met de wheel-URL en niet `python -m spacy download`:
    die laatste roept pip aan, en een door uv beheerde omgeving heeft geen pip,
    dus dat loopt vast op een verwarrende foutmelding.
    """
    naam = _volledige_naam(keuze)
    sleutel = MODEL_PER_NAAM.get(naam)
    if sleutel is None:
        raise ValueError(f"Onbekend model: {keuze}")
    return f"uv pip install {MODELLEN[sleutel].wheel}"

# Nederlandse afkortingen die op een punt eindigen. Zonder deze lijst telt
# "Hij kwam om 9 uur, d.w.z. te laat." als drie zinnen in plaats van één, en
# dat vertekent elke formule die door het aantal zinnen deelt.
AFKORTINGEN = (
    "bijv.", "bijz.", "blz.", "bv.", "ca.", "cf.", "d.w.z.", "dhr.", "dr.",
    "drs.", "e.a.", "e.d.", "e.v.", "enz.", "etc.", "evt.", "excl.", "fig.",
    "i.p.v.", "i.v.m.", "incl.", "ing.", "ir.", "jl.", "jr.", "m.a.w.",
    "m.b.t.", "m.b.v.", "m.i.", "m.n.", "max.", "mevr.", "min.", "mr.", "mw.",
    "n.a.v.", "n.Chr.", "nl.", "nr.", "o.a.", "o.b.v.", "o.i.d.", "p.a.",
    "prof.", "resp.", "t.b.v.", "t.o.v.", "v.Chr.", "vgl.", "z.g.", "zgn.",
)


def haal_nlp(model_naam: str | None = None):
    """
    De gedeelde spaCy-pijplijn. Laadt het model bij de eerste aanroep.

    NER staat uit: we gebruiken alleen POS-tags, lemma's en dependencies, en
    het uitschakelen scheelt merkbaar tijd over een heel manuscript.
    """
    global _nlp, _geladen_model

    naam = _volledige_naam(model_naam) if model_naam else huidig_model()
    if _nlp is not None and _geladen_model == naam:
        return _nlp

    import spacy

    try:
        _nlp = spacy.load(naam, exclude=["ner"])
    except OSError as fout:
        melding = [f"Het spaCy-model '{naam}' is niet gevonden."]
        if naam == STANDAARDMODEL:
            melding.append("Draai eerst:  uv sync --group nl")
        else:
            melding.append("Installeer het met:")
            melding.append(f"  {installatieopdracht(naam)}")
            melding.append("of kies een ander model:  ./nl/run_nl.sh taalmodel sm")
        melding.append(f"(oorspronkelijke fout: {fout})")
        raise SystemExit("\n".join(melding)) from fout

    _geladen_model = naam

    for afkorting in AFKORTINGEN:
        _nlp.tokenizer.add_special_case(afkorting, [{"ORTH": afkorting}])

    # Een lang hoofdstuk mag de standaardlimiet niet raken.
    _nlp.max_length = max(_nlp.max_length, 2_000_000)
    return _nlp


def verwerk(teksten, batch_grootte: int = 8):
    """Ontleed meerdere teksten in één doorloop; geeft een generator van Docs."""
    return haal_nlp().pipe(list(teksten), batch_size=batch_grootte)


def ontleed(tekst: str):
    """Ontleed één tekst."""
    return haal_nlp()(tekst)


# ---------------------------------------------------------------
# Tokens filteren
# ---------------------------------------------------------------

def is_woord(token) -> bool:
    """
    Telt dit token mee als woord?

    Leestekens, spaties en losse cijfers vallen af. Dit is de definitie die
    overal in de tool geldt, zodat woordentallen tussen modules overeenkomen.
    """
    return not (token.is_punct or token.is_space or token.like_num) and any(
        teken.isalpha() for teken in token.text
    )


def woorden(doc) -> list:
    """De tokens die als woord meetellen."""
    return [t for t in doc if is_woord(t)]


def zinnen(doc) -> list:
    """De zinnen met minstens één woord erin."""
    return [z for z in doc.sents if any(is_woord(t) for t in z)]
