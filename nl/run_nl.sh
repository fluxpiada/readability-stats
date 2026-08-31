#!/usr/bin/env bash
# run_nl.sh — Nederlandse leesbaarheidsanalyse, in één opdracht.
#
#   ./nl/run_nl.sh                          menu, vraagt om de map
#   ./nl/run_nl.sh rapport /pad/naar/tekst  meteen het volledige rapport
#   ./nl/run_nl.sh stijl   /pad/naar/tekst  alleen de stijlanalyse
#
# Installeert uv als het ontbreekt en laat uv Python, pakketten en het
# taalmodel regelen.

set -euo pipefail
cd "$(dirname "$0")/.."

# --- 1. uv beschikbaar maken -------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "uv niet gevonden — wordt geïnstalleerd via astral.sh ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
    command -v uv >/dev/null 2>&1 || {
        echo "uv staat nog niet in het PATH. Open een nieuwe terminal en probeer opnieuw."
        exit 1
    }
fi

# --- 2. omgeving klaarzetten -------------------------------------------------
# De groep 'nl' bevat spaCy, het Nederlandse taalmodel, pyphen en wordfreq.
# De eerste keer duurt dit even: er wordt ongeveer 100 MB opgehaald.
#
# --inexact is hier wezenlijk: zonder die vlag maakt `uv sync` de omgeving
# precies gelijk aan uv.lock en gooit het dus alles eruit wat daar niet in staat.
# De modellen md en lg worden met `uv pip install` opgehaald en staan niet in de
# lock, dus die werden bij de volgende start weer verwijderd — het model was dan
# "opgehaald" maar meteen weer weg.
echo "Omgeving controleren ..."
uv sync --quiet --inexact --group nl

OPDRACHTEN=(rapport leesbaarheid stijl dialoog woorden taalmodel)

opdracht="${1:-}"
map="${2:-}"

if [ -z "$opdracht" ]; then
    echo
    echo "Nederlandse leesbaarheidsanalyse"
    echo "--------------------------------"
    echo "  1) rapport       volledig rapport (markdown + PDF + grafieken)"
    echo "  2) leesbaarheid  Flesch-Douma en Leesindex A per hoofdstuk"
    echo "  3) stijl         lijdende vorm, tangconstructies, schrapwoorden"
    echo "  4) dialoog       dialoogaandeel, consistentie en tempo"
    echo "  5) woorden       moeilijke woorden en woordvariatie"
    echo "  6) taalmodel     nauwkeuriger taalmodel kiezen of installeren"
    echo
    read -r -p "Kies [1-6]: " keuze
    case "$keuze" in
        1|2|3|4|5|6) opdracht="${OPDRACHTEN[$((keuze - 1))]}" ;;
        *) echo "Onbekende keuze: $keuze"; exit 1 ;;
    esac
fi

# --- taalmodel: geen manuscriptmap nodig ------------------------------------
if [ "$opdracht" = "taalmodel" ]; then
    if [ -z "$map" ]; then
        uv run --group nl python nl/analyseer.py taalmodel
        echo
        read -r -p "Welk model wilt u gebruiken? [sm/md/lg, leeg = laten staan]: " model
        [ -z "$model" ] && exit 0
    else
        model="$map"
    fi

    uv run --group nl python nl/analyseer.py taalmodel "$model" || exit 1

    # Ophalen als het er nog niet is. `python -m spacy download` werkt hier niet:
    # dat roept pip aan, en een door uv beheerde omgeving heeft geen pip.
    wheel=$(uv run --group nl python -c "
import sys; sys.path.insert(0, 'nl')
from leesbaarheid import taal
naam = taal._volledige_naam('$model')
print('' if taal.is_geinstalleerd(naam) else taal.MODELLEN[taal.MODEL_PER_NAAM[naam]].wheel)
")
    if [ -n "$wheel" ]; then
        echo
        read -r -p "Het model is nog niet geïnstalleerd. Nu ophalen? [J/n]: " ja
        case "${ja:-J}" in
            [JjYy]*) uv pip install "$wheel" ;;
            *) echo "Overgeslagen. Later zelf: uv pip install $wheel" ;;
        esac
    fi
    exit 0
fi

if [ -z "$map" ]; then
    echo "(tip: u kunt de map vanuit Finder op dit venster slepen)"
    read -r -e -p "Map met uw .md- of .docx-bestanden: " map
fi

# Een gesleept of geplakt pad komt letterlijk binnen: aanhalingstekens,
# backslashes voor spaties en ~ zijn dan nog niet door de shell verwerkt.
map="${map#\"}" ; map="${map%\"}"
map="${map#\'}" ; map="${map%\'}"
map="${map//\\ / }"
map="${map/#\~/$HOME}"
map="${map%/}"

if [ ! -d "$map" ]; then
    echo
    echo "Dit is geen map: $map"
    echo "Geef een bestaande map met .md- of .docx-bestanden, bijvoorbeeld:"
    echo "  ./nl/run_nl.sh $opdracht \"\$HOME/Documenten/mijn-boek\""
    exit 1
fi

echo
# Een lege derde parameter niet doorgeven: argparse zou die als uitvoermap zien.
if [ -n "${3:-}" ]; then
    uv run --group nl python nl/analyseer.py "$opdracht" "$map" "$3"
else
    uv run --group nl python nl/analyseer.py "$opdracht" "$map"
fi
