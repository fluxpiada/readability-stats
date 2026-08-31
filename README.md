# readability-stats

Python scripts that analyse the readability, pacing and vocabulary of a manuscript
made of `.md` or `.docx` files — one file per chapter — and draw a few graphs along the way.

The scripts in this root folder are English through and through: Flesch, Flesch-Kincaid and Gunning Fog are all calibrated on English, the syllable
counter strips accented characters (`één` becomes `n`), and it applies the English silent-`e` rule to a language where the final `e` is pronounced.

> [!IMPORTANT]
> **Werkt u aan een Nederlands manuscript?** Gebruik dan [`nl/`](nl/README.md).
>
> `nl/` is a self-contained Dutch version built on Flesch-Douma (1960) and
> Brouwer's Leesindex A (1963), with frequency-based word difficulty that
> handles Dutch compounds, plus passive-voice, tangconstructie and dialogue
> analysis.
> 
> Start it with `./nl/run_nl.sh`, or `.\nl\run_nl.ps1` on Windows.

---

## Quick start

Everything runs through [uv](https://docs.astral.sh/uv/) from Astral. You do **not** need to
install Python or any packages yourself — uv fetches the right Python version and all
dependencies into a local `.venv/` on first run.

**macOS / Linux** — clone and run:

```bash
git clone https://github.com/<your-user>/readability-stats.git
cd readability-stats
./run.sh
```

**Windows** — the same thing in PowerShell:

```powershell
git clone https://github.com/<your-user>/readability-stats.git
cd readability-stats
.\run.ps1
```

If PowerShell refuses to run the script ("running scripts is disabled on this system"), either
run it as `powershell -ExecutionPolicy Bypass -File .\run.ps1`, or allow local scripts once
with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

> [!WARNING]
> **The Windows runners have not been tested on Windows yet.** `run.ps1` and `nl/run_nl.ps1`
> were written and reviewed against their bash twins, but every run so far has been on macOS.
> If something breaks — the uv install, the folder prompt, a step that will not start — please
> open an issue with the error text and your PowerShell version (`$PSVersionTable.PSVersion`).
> The analysis code underneath is platform-independent and is covered by the test suite; it is
> the runner scripts that need a real Windows machine to confirm.

Both runners install uv if it is missing, sync the environment, then ask which analysis to run
and which folder to point at. `run.ps1` is a direct translation of `run.sh` — same steps, same
menu, same arguments.

Non-interactive forms:

```bash
./run.sh 01 ~/Documents/my-book/manuscript    # one step
./run.sh all ~/Documents/my-book/manuscript   # every step, in order
```

```powershell
.\run.ps1 01 C:\Users\you\Documents\my-book\manuscript    # one step
.\run.ps1 all C:\Users\you\Documents\my-book\manuscript   # every step, in order
```

Write Windows paths out in full rather than using `~`: PowerShell hands `~` to the script
unexpanded, where bash would have expanded it first.

### The report

Step 8 is the one to run if you want something to keep rather than something to read in the
terminal. It runs every analysis in a single pass and writes both formats:

```bash
./run.sh 8 ~/Documents/my-book/manuscript                  # macOS / Linux
```

```powershell
.\run.ps1 8 C:\Users\you\Documents\my-book\manuscript      # Windows
```

Every run is snapshotted into its own timestamped folder and never overwrites an earlier one,
so you can watch the manuscript change across drafts:

```text
reports/
├── index.md                    every snapshot, with the change from the run before it
├── latest -> 2026-08-30-1930   symlink to the newest, so one path always works
├── 2026-08-24-1102/
└── 2026-08-30-1930/
    ├── report.md               all tables, diffs cleanly between drafts
    ├── report.pdf              the same content, laid out — hand this to an editor
    ├── pacing_curve.png        embedded in both
    └── summary.json            the headline figures, used to build index.md
```

`reports/index.md` is the one to open when you want the trend rather than a single run — it
tables every snapshot with the change in word count and mean Flesch since the previous one:

```text
| Snapshot        | Chapters | Words  | Words change | Mean Flesch | Flesch change |
| 2026-08-24-1102 | 32       | 78,410 | —            | 62.1        | —             |
| 2026-08-30-1930 | 34       | 81,255 | +2,845       | 60.4        | -1.7          |
```

It is rebuilt from the `summary.json` files on every run, so deleting a snapshot folder is all
it takes to drop it from the index.

On Windows the `latest` link is only created if Developer Mode is on, since that is what lets a
normal account make a symlink. Without it the link is quietly skipped: the timestamped folders
and `reports/index.md` are written exactly as above, and you open the newest folder by name.

To write somewhere specific instead — no timestamp, no snapshot, no index — pass a second
argument:

```bash
uv run 08_report.py ~/Documents/my-book/manuscript ~/Desktop/for-my-editor
```

Each report opens with a summary (chapter count, total words, estimated manuscript and
paperback pages), then the per-chapter table, the hardest-to-easiest ranking, the tightening
priority list, the chapter-to-chapter changes, the pacing curve, and finally a glossary
explaining what every statistic means and what it cannot tell you.

### Running a single script directly

If uv is already installed, you can skip the wrapper entirely. This is identical on every
platform apart from how the path is written:

```bash
uv run 01_readability.py ~/Documents/my-book/manuscript          # macOS / Linux
```

```powershell
uv run 01_readability.py C:\Users\you\Documents\my-book\manuscript   # Windows
```

`uv run` syncs the environment first, so there is no activate step and no `pip install`.

### Installing uv by hand

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS / Linux
brew install uv                                    # or via Homebrew
```

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows
winget install --id=astral-sh.uv                            # or via winget
```

### Input and output

Input is a **folder**. Every `.md` and `.docx` file below it is loaded recursively, sorted by
path, and treated as one chapter. Any path containing a folder named `draft` is skipped.
Markdown syntax (headings, links, emphasis, code blocks) is stripped before counting, so the
markup does not pollute the numbers.

Output files (`pacing_curve.png`, `converted_txt/`, `sentence_histograms/`) are written to the
directory you run from, not to the manuscript folder.

---

## What the analysis actually tells you

The scripts measure **surface features of the prose** — sentence length, syllable counts, word
variety — and turn them into a handful of established indices. These are proxies for effort:
they say how hard a page is to process, not whether it is any good. A tense, well-written
action scene and a badly written one can score the same. Use the numbers to find *outliers*
worth re-reading, not as a grade.

### Ranges and target zones at a glance

Table headers carry a symbol: **↑** higher is better, **↓** lower is better, **•** neither end
is better.

| Metric | Typical range | Better | Aim (fiction) | Where the target came from |
| --- | --- | --- | --- | --- |
| Flesch Reading Ease | 0–100, can fall outside | ↑ | 60–80 | Flesch's bands + convention |
| Flesch–Kincaid Grade | 1–18 (US grade) | ↓ | 5–9 | convention |
| Gunning Fog | 6–20 | ↓ | 6–10 | Gunning: under 12 |
| Average sentence length | 8–25 words | ↓ | 11–18 | ours |
| TTR | 0–1 | ↑ | *no target* — falls with length | — |
| MTLD | 10–200 | ↑ | 60–120 | ours |
| Chapter-to-chapter deltas | unbounded, ± | • | *no target* | — |
| Tightening score | relative to this manuscript | ↑ | *no target* — a running order | — |

Two things to keep straight.

**Not every statistic has a better end.** A large delta between chapters is not a fault — a
change of gear can be exactly right. TTR falls automatically as a chapter grows. Those say
outright that there is no target rather than inventing one. The tightening score is a running
order for revision, not a measurement: high means "re-read this first", not "this is worse".

**Most target zones are ours.** Flesch's interpretation bands are published; "60–80 for a
novel" is editorial convention. So each zone records where it came from. They live in
`read_stats.py` → `METRICS` if you want to tune them.

Falling outside a zone is not a failure. A heavy chapter is allowed to read heavy.

### The metrics

**Flesch Reading Ease** — a 0–100 score built from average sentence length and average
syllables per word. Higher is easier.

| Score | Reads like |
| --- | --- |
| 90–100 | very easy, short simple sentences |
| 60–70 | plain English, most popular fiction |
| 30–50 | dense — academic, technical, or heavily subordinated prose |
| below 30 | very hard going |

*Range 0–100 (can fall outside), higher is better. Aim for fiction: 60–80 — the bands are
Flesch's own, the fiction range is convention.*

**Flesch–Kincaid Grade** — the same inputs recast as a US school grade level. `8.0` means an
average eighth-grader could follow it. Most commercial fiction sits between 5 and 9.

*Range 1–18, lower is easier. Aim for fiction: 5–9 (convention).*

**Gunning Fog** — combines sentence length with the share of "complex" words (three or more
syllables). Sensitive to jargon and abstraction in a way Flesch is not. Roughly also a grade
level; under 12 is comfortable for a general reader.

*Range 6–20, lower is easier. Aim for fiction: 6–10 (Gunning: under 12 suits a general
reader).*

**Sentence length distribution** — a histogram per chapter. The *shape* matters more than the
average: a healthy scene usually mixes short punches with longer sentences. A narrow spike
means every sentence is the same length, which reads as monotone regardless of how good the
individual sentences are.

*Spread matters more than the mean; there is no target shape.*

**Lexical diversity (TTR and MTLD)** — how much of your vocabulary repeats.
*TTR* (type-token ratio) is unique words ÷ total words; it is simple but drops automatically
in longer chapters, so only compare chapters of similar length. *MTLD* corrects for that and is
the number to trust when chapter lengths differ. Low diversity can mean a tight, controlled
voice — or an unnoticed tic word.

*TTR 0–1 and MTLD 10–200, higher is more varied. Aim for MTLD 60–120 (ours); TTR has no
target because it falls automatically in longer chapters.*

**Chapter-to-chapter deltas** — how far readability, fog and word count jump between
consecutive chapters. Large swings are where the reading experience changes gear. Sometimes
that is deliberate pacing; sometimes it is a chapter that was written on a different day in a
different register.

*Unbounded, ±. Neither end is better: a change of gear can be deliberate, so there is no
target.*

**Pacing curve** — Flesch plotted against chapter order, over Flesch's interpretation bands,
with the 60–80 fiction target zone outlined. Dips are the dense stretches. Long flat runs are
where the texture stops changing. There is no "pass mark" line: leaving the zone is a question
to look at, not a fault.

**Tightening score** — a composite ranking that pushes chapters that are simultaneously wordy,
dense and low-readability to the top. It is a triage list for revision, nothing more: read the
top few chapters again before you decide anything.

*Relative to this manuscript, so there is no absolute range and no target. Higher means
"re-read this one first", not "this is worse writing".*

### What it does not measure

Plot, character, tension, dialogue quality, or whether a sentence is beautiful. Deliberately
difficult prose scores badly here, and short sentences score well even when they are dull.
Every index above rewards brevity, so do not optimise for the numbers — read the chapters they
point you at.

---

## Scripts

| Script | What it does |
| --- | --- |
| `01_readability.py` | Flesch, FK Grade, Gunning Fog per chapter; sorted summary table |
| `02_convert_md_txt.py` | Strips markdown and writes plain `.txt` files to `converted_txt/` |
| `03_readability_vs_story_order.py` | Plots Flesch score across chapter order → `pacing_curve.png` |
| `04_sentence_length_histo.py` | Sentence-length histogram per chapter → `sentence_histograms/` |
| `05_lexical_div.py` | TTR and MTLD lexical diversity per chapter |
| `06_complex_deltas.py` | Chapter-to-chapter deltas in Flesch, Fog, and word count |
| `07_tightening.py` | Ranks chapters by tightening priority (wordiness + density score) |
| `08_report.py` | Every statistic in one `report.md` + `report.pdf`, with the metrics explained |
| `countwords.py` | Word count per chapter, plus the manuscript total |

Steps 04, 05 and 08 download the NLTK `punkt` and `stopwords` data on first run. If that
download is not possible, step 08 drops the TTR/MTLD columns and notes it in the report rather
than failing.

## Shared code

`read_stats.py` holds everything shared: `strip_markdown`, `count_syllables`,
`readability_metrics`, `extract_docx`, `load_chapters`, the lexical-diversity functions
(`clean_tokens`, `ttr`, `mtld`), the `tightening_score` formula and `plot_pacing_curve`.
Edit there, not in the individual scripts — the report and the individual steps both read from
this module, so a formula changed here stays consistent across every output.

## Dependencies

Declared in `pyproject.toml` and pinned in `uv.lock`, so every machine gets the same versions.
`requirements.txt` is kept only for anyone who would rather use plain pip.
