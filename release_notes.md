# Release notes

## Cleanup pass — shared helpers, uv model groups, dead code

A quality pass over the whole project: reuse, simplification, efficiency and
altitude. No new features. Two deliberate behaviour changes are called out
below; everything else produces identical output.

### Shared helpers

`build_dataframe` had been copy-pasted verbatim into steps 03, 06 and 07, with
a fourth, drifted superset in `08_report.py`. It is now `chapter_frame()` in
`read_stats.py`, and those scripts are thin presenters over it.

The two Flesch band tables — one for the console, one for the chart — had
drifted apart: a chapter scoring 75 was "fairly easy" in the CLI and "easy" on
the chart of the same run. There is now one table with a `band()` accessor, so
the two cannot disagree. The same fix landed on the Dutch side, where the chart
re-declared bands that `formules.BANDEN` already owned. Both charts now draw
seven bands instead of five, which is the visible consequence of the tables
agreeing.

Path normalisation (stripping quotes, unescaping spaces, expanding `~`) moved
into `resolve_folder`, so a path typed at the Python prompt behaves like one
typed at `./run.sh`.

### spaCy models now live in uv dependency groups

`md` and `lg` moved into their own dependency groups, with their wheel URLs in
`pyproject.toml` under `[tool.uv.sources]`. All three models are therefore in
`uv.lock` with pinned versions, and `MODELVERSIE` — which had to be kept in step
with `pyproject.toml` by hand — is gone.

The launcher scripts no longer embed a Python one-liner reaching into three
`taal.py` internals (one of them private) to rebuild a wheel URL. Installation
is now `analyseer.py taalmodel <keuze> --installeer`, so the scripts know
nothing about wheels or groups.

**The launchers keep `--inexact`.** A group sync is exact with respect to the
groups you name, so a plain `uv sync --group nl` uninstalls `md` and `lg` — a
541 MB re-download, and precisely the bug the flag was added to prevent. The
five-line comment explaining this, previously duplicated across four scripts in
two languages, is now one accurate line each.

### Model selection at one altitude

`--model` used to work by side effect: it loaded a model purely to warm a
module-global cache that a later call would hit. If the resolved name differed
it loaded a second model — 541 MB twice for `lg` — and its `except ValueError`
caught an exception that could not be raised, so an invalid model name escaped
as a `SystemExit` from deeper down. There is now an explicit session override
(`taal.stel_model_in`) consulted first by `huidig_model()`, and `volledige_naam`
rejects unknown names, so the flag, the environment variable, the preference
file and the default all funnel through one resolver with one error path.

### Report prose follows the model that ran

The caveats, bibliography and licence table hardcoded `nl_core_news_sm`. With
`.taalmodel` set to `lg`, a report printed "Taalmodel: nl_core_news_lg" in its
summary and then told the reader, three sections later, that the numbers came
from the small model and licensed it accordingly. Those strings are now
generated from the model that actually ran.

### Efficiency

- **English MTLD is now the bidirectional McCarthy & Jarvis algorithm.**
  The previous forward-only pass reported a different number depending on which
  end of the chapter it started from. **Reported MTLD values change.**
- The O(n²) set rebuild inside MTLD is gone (incremental set).
- Syllables are counted once per word rather than twice, and cached.
- The NLTK stopword corpus is no longer re-read from disk once per chapter.
- `nltk.download` no longer makes a network round-trip per package per run when
  the corpora are already present.
- Each spaCy `Doc` was being walked about seven times per chapter; words and
  sentences are now computed once and passed down.
- The Dutch report DataFrame was rebuilt seven times per run, and the table set
  twice; both are now built once in `maak_rapport`.
- `countwords.py` no longer runs a full readability analysis to read one number.
- `Pyphen` and `python-docx` load lazily instead of at import.

### Dead code

Removed six dataclass fields nothing read (`passief_zonder_agens`, `tang_zinnen`,
`schrapwoord_telling`, `gemiddelde_dialoogregel`, `conventies_gevonden`,
`Leesbaarheid._bron`), a `CONVENTIES` table shadowed by `_OPENERS`, a
`conventie` parameter on `is_dialoogalinea` that could not change its result,
`tel_lettergrepen_reeks` (no callers), and a one-entry `__all__`.

Menu bounds in all four launchers now derive from the step list rather than a
hardcoded `[1-9]`, and the Dutch menu text and command list are one array, so
reordering cannot silently run the wrong command.

### Verification

All 295 tests pass. The English `report.md` is byte-identical across the table
refactor; the Dutch `rapport.md` differs only in its timestamp. All eight
English steps and all five Dutch subcommands were run end to end.

The PowerShell twins were updated to match their shell counterparts but, as
elsewhere in this repo, have not been run on a Windows machine.
