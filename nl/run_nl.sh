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
# --inexact: een sync maakt de omgeving precies gelijk aan de genoemde groepen.
# De grotere modellen md en lg staan in hun eigen groep (nl-md, nl-lg), dus
# zonder deze vlag zou elke start het gekozen model weer verwijderen.
echo "Omgeving controleren ..."
uv sync --quiet --inexact --group nl

# Eén lijst: naam en omschrijving samen, zodat het menu en wat er draait niet
# uit elkaar kunnen lopen.
OPDRACHTEN=(
    "rapport|volledig rapport (markdown + PDF + grafieken)"
    "leesbaarheid|Flesch-Douma en Leesindex A per hoofdstuk"
    "stijl|lijdende vorm, tangconstructies, schrapwoorden"
    "dialoog|dialoogaandeel, consistentie en tempo"
    "woorden|moeilijke woorden en woordvariatie"
    "taalmodel|nauwkeuriger taalmodel kiezen of installeren"
)

opdracht="${1:-}"
map="${2:-}"

if [ -z "$opdracht" ]; then
    echo
    echo "Nederlandse leesbaarheidsanalyse"
    echo "--------------------------------"
    for i in "${!OPDRACHTEN[@]}"; do
        naam="${OPDRACHTEN[$i]%%|*}"
        uitleg="${OPDRACHTEN[$i]#*|}"
        printf "  %d) %-13s %s\n" "$((i + 1))" "$naam" "$uitleg"
    done
    echo
    read -r -p "Kies [1-${#OPDRACHTEN[@]}]: " keuze
    if ! [ "$keuze" -ge 1 ] 2>/dev/null || [ "$keuze" -gt "${#OPDRACHTEN[@]}" ]; then
        echo "Onbekende keuze: $keuze"
        exit 1
    fi
    opdracht="${OPDRACHTEN[$((keuze - 1))]%%|*}"
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

    # --installeer haalt het model op als het er nog niet is. Welke groep
    # daarvoor nodig is weet analyseer.py; dit script hoeft dat niet te weten.
    uv run --group nl python nl/analyseer.py taalmodel "$model" --installeer
    exit $?
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
