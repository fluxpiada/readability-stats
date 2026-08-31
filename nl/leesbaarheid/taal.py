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

import os

_nlp = None

STANDAARDMODEL = "nl_core_news_sm"

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


def haal_nlp():
    """
    De gedeelde spaCy-pijplijn. Laadt het model bij de eerste aanroep.

    NER staat uit: we gebruiken alleen POS-tags, lemma's en dependencies, en
    het uitschakelen scheelt merkbaar tijd over een heel manuscript.
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    import spacy

    naam = os.environ.get("RS_SPACY_MODEL", STANDAARDMODEL)
    try:
        _nlp = spacy.load(naam, exclude=["ner"])
    except OSError as fout:
        raise SystemExit(
            f"Het spaCy-model '{naam}' is niet gevonden.\n"
            f"Draai eerst:  uv sync --group nl\n"
            f"(oorspronkelijke fout: {fout})"
        ) from fout

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
