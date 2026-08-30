#!/usr/bin/env bash
# run.sh — one-command runner for readability-stats.
#
#   ./run.sh                      interactive menu, asks for the folder
#   ./run.sh 01 /path/to/text     run step 01 on that folder
#   ./run.sh all /path/to/text    run every step in order
#
# Installs uv (astral.sh) if it is missing, then lets uv handle Python and deps.

set -euo pipefail
cd "$(dirname "$0")"

# --- 1. make sure uv is available -------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found — installing from astral.sh ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # the installer drops uv in ~/.local/bin (or $XDG_BIN_HOME)
    export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
    command -v uv >/dev/null 2>&1 || {
        echo "uv still not on PATH. Open a new shell and re-run ./run.sh"
        exit 1
    }
fi

# --- 2. sync the environment (downloads Python 3.12 if needed) --------------
uv sync --quiet

# --- 3. figure out what to run ----------------------------------------------
STEPS=(
    "01_readability.py"
    "02_convert_md_txt.py"
    "03_readability_vs_story_order.py"
    "04_sentence_length_histo.py"
    "05_lexical_div.py"
    "06_complex_deltas.py"
    "07_tightening.py"
    "08_report.py"
    "countwords.py"
)

choice="${1:-}"
folder="${2:-}"

if [ -z "$choice" ]; then
    echo
    echo "readability-stats"
    echo "-----------------"
    for i in "${!STEPS[@]}"; do
        printf "  %d) %s\n" "$((i + 1))" "${STEPS[$i]}"
    done
    echo "  a) all of the above"
    echo
    read -r -p "Choose [1-9 or a]: " choice
fi

if [ -z "$folder" ]; then
    echo "(tip: you can drag the folder from Finder onto this window)"
    read -r -e -p "Folder with your .md / .docx files: " folder
fi

# A path typed or dragged into a prompt is not processed by the shell, so
# quotes, backslash-escaped spaces and ~ all arrive here literally.
folder="${folder#\"}" ; folder="${folder%\"}"
folder="${folder#\'}" ; folder="${folder%\'}"
folder="${folder//\\ / }"
folder="${folder/#\~/$HOME}"
folder="${folder%/}"

if [ ! -d "$folder" ]; then
    echo
    echo "Not a folder: $folder"
    echo "Pass an existing directory of .md / .docx files, e.g."
    echo "  ./run.sh $choice \"\$HOME/Documents/my-book/manuscript\""
    exit 1
fi

run_step() {
    echo
    echo "==> $1"
    uv run "$1" "$folder"
}

case "$choice" in
    a | all | A)
        for s in "${STEPS[@]}"; do run_step "$s"; done
        ;;
    [1-9] | 0[1-9])
        idx=$((10#$choice - 1))
        run_step "${STEPS[$idx]}"
        ;;
    *)
        echo "Unknown choice: $choice (expected 1-9 or 'all')"
        exit 1
        ;;
esac
