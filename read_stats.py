"""
read_stats.py — shared helpers for readability-stats
"""

import os
import re
import sys
from functools import lru_cache
from pathlib import Path


# -----------------------------------------------
# What each number means: range, direction, target
# -----------------------------------------------
#
# Without this, a figure in a report is meaningless: is 58 good, and which way
# is up? This table says, per column, what the range is, which end is better,
# and roughly where a novel should land.
#
# Two things on purpose:
#
# 1. Some statistics have no better end. Chapter-to-chapter deltas are not
#    "better" when small — a change of gear may be exactly right. TTR falls
#    automatically as a chapter grows. Those get "none" as their direction and
#    say outright that there is no target, rather than inventing a range.
# 2. Most target zones are ours, not published. Flesch's interpretation bands
#    are published; "60-80 for a novel" is editorial convention. So each zone
#    records where it came from.

from typing import NamedTuple

DIRECTIONS = ("higher", "lower", "none")
SYMBOLS = {"higher": "↑", "lower": "↓", "none": "•"}

NO_TARGET = "no target"


class Metric(NamedTuple):
    """How to read a column."""

    label: str
    span: str        # typical range, not necessarily a hard bound
    better: str      # higher | lower | none
    target: str      # roughly where a novel lands
    source: str      # where that target came from

    @property
    def symbol(self) -> str:
        return SYMBOLS[self.better]

    @property
    def has_target(self) -> bool:
        return not self.target.startswith(NO_TARGET)


METRICS: dict[str, Metric] = {
    "flesch": Metric(
        "Flesch", "0-100 (can fall outside)", "higher", "60-80",
        "bands are Flesch's own; the fiction range is convention",
    ),
    "fk": Metric(
        "FK", "1-18 (US grade)", "lower", "5-9", "convention for commercial fiction",
    ),
    "fog": Metric(
        "Fog", "6-20", "lower", "6-10", "Gunning: under 12 suits a general reader",
    ),
    "avg_sent": Metric(
        "Avg len", "8-25 words", "lower", "11-18", "ours",
    ),
    "ttr": Metric(
        "TTR", "0-1", "higher",
        f"{NO_TARGET} — falls automatically in longer chapters", "none",
    ),
    "mtld": Metric("MTLD", "10-200", "higher", "60-120", "ours"),
    "delta": Metric(
        "Change", "unbounded, ±", "none",
        f"{NO_TARGET} — a change of gear can be deliberate", "none",
    ),
    "tightening": Metric(
        "Score", "relative to this manuscript", "higher",
        f"{NO_TARGET} — a running order for revision, not a measurement", "none",
    ),
}


def header(key: str, label: str | None = None) -> str:
    """Column header with its direction symbol appended."""
    metric = METRICS.get(key)
    if metric is None:
        return label or key
    return f"{label or metric.label} {metric.symbol}"


def legend(keys) -> str:
    """
    One line under a table: what the symbols mean and where to aim. Only covers
    the columns in that table, so a header can never show a symbol the legend
    does not explain.
    """
    present = [k for k in keys if k in METRICS]
    if not present:
        return ""

    used = {METRICS[k].better for k in present}
    meaning = {
        "higher": f"{SYMBOLS['higher']} higher is better",
        "lower": f"{SYMBOLS['lower']} lower is better",
        "none": f"{SYMBOLS['none']} neither end is better",
    }
    lines = [" · ".join(meaning[d] for d in DIRECTIONS if d in used)]

    aims = [f"{METRICS[k].label} {METRICS[k].target}"
            for k in present if METRICS[k].has_target]
    if aims:
        lines.append("Aim for fiction: " + " · ".join(aims))

    return "\n".join(lines)


def range_note(key: str) -> str:
    """The range/direction/target sentence for the glossary."""
    metric = METRICS.get(key)
    if metric is None:
        return ""
    direction = {
        "higher": "higher is better",
        "lower": "lower is better",
        "none": "neither end is better",
    }[metric.better]
    aim = (f"Aim for fiction: {metric.target} ({metric.source})."
           if metric.has_target else f"{metric.target.capitalize()}.")
    return f"Range {metric.span}, {direction}. {aim}"


# -----------------------------------------------
# Unicode font for the PDF
# -----------------------------------------------

def register_unicode_font() -> str:
    """
    Register DejaVuSans with reportlab and return the font name to use.

    Needed because the direction arrows above are not in WinAnsi, and
    reportlab's built-in Helvetica drops such characters *silently* — the
    arrows would simply not appear and nothing would report an error.
    DejaVuSans ships with matplotlib, so this costs no extra dependency.

    Returns "Helvetica" if registration fails, so a report still gets written.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    name = "DejaVuSans"
    if name in pdfmetrics.getRegisteredFontNames():
        return name

    try:
        import matplotlib
        ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        pdfmetrics.registerFont(TTFont(name, str(ttf / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(f"{name}-Bold", str(ttf / "DejaVuSans-Bold.ttf")))
        from reportlab.lib.fonts import addMapping
        addMapping(name, 0, 0, name)
        addMapping(name, 1, 0, f"{name}-Bold")
        return name
    except Exception as exc:
        print(f"  note: Unicode font not loaded ({exc});")
        print("  direction arrows may be missing from the PDF.")
        return "Helvetica"


# -----------------------------------------------
# Interactive folder prompt
# -----------------------------------------------

def normalise_path(raw: str) -> str:
    """
    Clean up a path that was dragged in or pasted rather than typed.

    Such a path arrives literally: still wrapped in quotes, with backslashes in
    front of spaces and an unexpanded ~, because no shell has touched it. The
    launcher scripts do this same cleanup before they hand a path over, so
    doing it here means a path typed at the Python prompt behaves the same way.
    """
    path = raw.strip()
    for quote in ('"', "'"):
        if len(path) > 1 and path.startswith(quote) and path.endswith(quote):
            path = path[1:-1]
            break
    path = path.replace("\\ ", " ")
    path = os.path.expanduser(path)
    # A trailing separator is harmless but makes paths compare unequal.
    if len(path) > 1:
        path = path.rstrip(os.sep)
    return path


def resolve_folder(default: str | None = None) -> str:
    """
    Return the folder to analyse, in this priority order:
      1. CLI argument (sys.argv[1]) if provided
      2. Interactive prompt if running in a terminal
      3. *default* if supplied and no input given
    Raises SystemExit if nothing is available.
    """
    if len(sys.argv) > 1:
        return normalise_path(sys.argv[1])

    if sys.stdin.isatty():
        prompt = "Folder to analyse"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        answer = input(prompt).strip()
        if answer:
            return normalise_path(answer)

    if default:
        return normalise_path(default)

    print("Error: no folder specified. Pass a path as the first argument.")
    raise SystemExit(1)


# -----------------------------------------------
# Markdown → plain text
# -----------------------------------------------

def strip_markdown(md: str) -> str:
    text = md
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)   # fenced code blocks
    text = re.sub(r"`[^`]+`", "", text)                       # inline code
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)               # images
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)           # links → keep label
    text = re.sub(r"(^|\n)[#>\-\*\+]+\s*", r"\1", text)      # headings / lists / blockquotes
    text = re.sub(r"[*_]{1,3}", "", text)                     # emphasis markers
    return text


# -----------------------------------------------
# Syllable counter
# -----------------------------------------------

# Cached because natural language repeats itself: across a manuscript the great
# majority of calls are for a word already counted.
@lru_cache(maxsize=100_000)
def count_syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0

    vowels = "aeiouy"
    syllables = 0
    prev_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            syllables += 1
        prev_vowel = is_vowel

    # silent e
    if word.endswith("e") and syllables > 1:
        syllables -= 1

    return max(1, syllables)


# -----------------------------------------------
# Readability metrics (Flesch, FK Grade, Fog)
# -----------------------------------------------

WORD_RE = re.compile(r"\b[\w']+\b")


def count_words(text: str) -> int:
    """How many words this text holds, by the same rule the formulas use."""
    return sum(1 for _ in WORD_RE.finditer(text))


def readability_metrics(text: str) -> dict | None:
    words = WORD_RE.findall(text)
    word_count = len(words)

    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_count = len(sentences)

    if sentence_count == 0 or word_count == 0:
        return None

    counts = [count_syllables(w) for w in words]
    syllable_count = sum(counts)
    complex_words = sum(1 for c in counts if c >= 3)

    flesch   = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    fog      = 0.4 * ((word_count / sentence_count) + 100 * (complex_words / word_count))

    return {
        "words":       word_count,
        "sentences":   sentence_count,
        "syllables":   syllable_count,
        "flesch":      flesch,
        "fk_grade":    fk_grade,
        "gunning_fog": fog,
    }


# -----------------------------------------------
# Word (.docx) → plain text
# -----------------------------------------------

def extract_docx(path: Path) -> str:
    """
    Extract plain text from a .docx file (requires python-docx).

    Imported here rather than at module level: python-docx pulls in lxml, and
    most of the scripts never open a .docx at all.
    """
    try:
        import docx  # python-docx
    except ImportError as exc:
        raise ImportError(
            "python-docx is not installed. Run: uv sync"
        ) from exc
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


# -----------------------------------------------
# Chapter loader
# -----------------------------------------------

SUPPORTED_EXTENSIONS = {".md", ".docx"}

def load_chapters(folder: str) -> list[tuple[str, str]]:
    """
    Recursively load all .md and .docx files under *folder*,
    skipping any path that contains a component named 'draft'.
    Returns a sorted list of (filename, plain_text) tuples.
    """
    chapters = []
    base = Path(folder)

    candidates = sorted(
        p for p in base.rglob("*")
        if p.suffix.lower() in SUPPORTED_EXTENSIONS and "draft" not in p.parts
    )

    for path in candidates:
        if path.suffix.lower() == ".docx":
            try:
                text = extract_docx(path)
            except ImportError as e:
                print(f"Skipping {path.name}: {e}")
                continue
        else:
            text = strip_markdown(path.read_text(encoding="utf-8"))

        chapters.append((path.name, text))

    return chapters


# -----------------------------------------------
# Lexical diversity (TTR, MTLD)
# -----------------------------------------------
#
# nltk is imported lazily: only scripts that actually measure lexical
# diversity should pay for the import and the corpus download.

_NLTK_READY: bool | None = None


def ensure_nltk_data() -> bool:
    """
    Download the punkt/stopwords corpora once per process.
    Returns False if they are unavailable (offline, or no writable cache),
    so callers can degrade instead of crashing.
    """
    global _NLTK_READY
    if _NLTK_READY is None:
        try:
            import nltk
            from nltk.corpus import stopwords

            # Look before downloading: nltk.download fetches and parses the
            # remote package index even when the corpus is already present, so
            # calling it unconditionally costs a network round-trip per run.
            for package, path in (
                ("punkt", "tokenizers/punkt"),
                ("punkt_tab", "tokenizers/punkt_tab"),
                ("stopwords", "corpora/stopwords"),
            ):
                try:
                    nltk.data.find(path)
                except LookupError:
                    nltk.download(package, quiet=True)
            stopwords.words("english")   # forces a real lookup, so missing data fails here
            _NLTK_READY = True
        except Exception:
            _NLTK_READY = False
    return _NLTK_READY


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    """
    The English stopword set, read once.

    NLTK re-reads the corpus file from disk on every stopwords.words() call,
    and clean_tokens runs once per chapter.
    """
    from nltk.corpus import stopwords

    return frozenset(stopwords.words("english"))


def clean_tokens(text: str) -> list[str]:
    """Lowercased word tokens, minus stopwords and punctuation."""
    import string
    from nltk.tokenize import word_tokenize

    stop = _stopwords()
    tokens = [w.lower() for w in word_tokenize(text)]
    return [t for t in tokens if t not in stop and t not in string.punctuation]


def ttr(tokens: list[str]) -> float:
    """Type-token ratio — naive but fast."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def _mtld_run(tokens: list[str], threshold: float) -> float:
    """One directional pass: how many factors the token stream breaks into."""
    factors = 0.0
    segment: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        segment.append(token)
        seen.add(token)
        if len(seen) / len(segment) < threshold:
            factors += 1
            segment, seen = [], set()

    if segment:
        ratio = len(seen) / len(segment)
        # partial factor: how far this leftover segment got towards the threshold
        if ratio < 1.0:
            factors += (1 - ratio) / (1 - threshold)

    if not factors:
        # No segment ever dropped below the threshold, i.e. every word is new.
        # That is maximum diversity, and the convention is to return the text
        # length — not 0, which would mean the opposite.
        return float(len(tokens))

    return len(tokens) / factors


def mtld(tokens: list[str], threshold: float = 0.72) -> float:
    """
    Measure of Textual Lexical Diversity (McCarthy & Jarvis).

    Measured in both directions and averaged, as the published algorithm
    specifies: a forward-only pass reports a different number depending on
    which end of the chapter it starts from. The Dutch twin of this function
    is `nl/leesbaarheid/woordenschat.mtld`.
    """
    if not tokens:
        return 0.0
    forward = _mtld_run(tokens, threshold)
    backward = _mtld_run(list(reversed(tokens)), threshold)
    if not forward or not backward:
        return forward or backward
    return (forward + backward) / 2


# -----------------------------------------------
# Tightening score
# -----------------------------------------------

def tightening_score(df):
    """
    Composite revision-priority score: wordy + dense + long-sentenced + hard to read.
    Takes a DataFrame with fog / fk / words / flesch columns, returns a Series.
    """
    return (
        df["fog"] * 0.5
        + df["fk"] * 0.3
        + df["words"] * 0.0005
        + (df["flesch"].max() - df["flesch"]) * 0.3
    )


# -----------------------------------------------
# Per-chapter table
# -----------------------------------------------

def chapter_frame(folder: str, lexical: bool = False):
    """
    Load *folder* and return (per-chapter stats, whether lexical diversity was
    measured).

    Every script that tabulates chapters starts here, so the column names are
    defined once. Deltas and the tightening score are always present: they are
    derived from the rows already in hand and cost nothing to add.

    *lexical* additionally measures TTR and MTLD, which needs NLTK's corpora;
    the returned flag says whether that succeeded, so callers can drop those
    columns rather than crash when the data cannot be downloaded.

    pandas is imported here because the scripts that only print text should not
    pay for it.
    """
    import pandas as pd

    lexical_ok = lexical and ensure_nltk_data()
    rows = []

    for i, (filename, text) in enumerate(load_chapters(folder)):
        m = readability_metrics(text)
        if not m:
            continue

        row = {
            "chapter":   filename,
            "order":     i,
            "words":     m["words"],
            "sentences": m["sentences"],
            "avg_sent":  m["words"] / m["sentences"],
            "flesch":    m["flesch"],
            "fk":        m["fk_grade"],
            "fog":       m["gunning_fog"],
        }

        if lexical_ok:
            tokens = clean_tokens(text)
            row["ttr"] = ttr(tokens)
            row["mtld"] = mtld(tokens)

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df, lexical_ok

    df["delta_flesch"] = df["flesch"].diff()
    df["delta_fog"] = df["fog"].diff()
    df["delta_words"] = df["words"].diff()
    df["tightening"] = tightening_score(df)
    return df, lexical_ok


# -----------------------------------------------
# Pacing curve plot
# -----------------------------------------------

# Flesch's published interpretation bands: the name a score gets in the console
# and the background shading on the chart, from one table so the two can never
# call the same score by different words.
FLESCH_BANDS = [
    (90, 100, "#e8f5e9", "very easy"),
    (80, 90, "#f1f8e9", "easy"),
    (70, 80, "#f9fbe7", "fairly easy"),
    (60, 70, "#fffde7", "standard"),
    (50, 60, "#fff3e0", "fairly difficult"),
    (30, 50, "#fbe9e7", "difficult"),
    (0, 30, "#ffebee", "very hard going"),
]


def band(score: float) -> str:
    """The interpretation band a Flesch score falls in."""
    for floor, _, _, name in FLESCH_BANDS:
        if score >= floor:
            return name
    return FLESCH_BANDS[-1][3]


def plot_pacing_curve(df, output_path: str = "pacing_curve.png") -> Path:
    """
    Plot Flesch score against chapter order. Returns the written path.

    The background is Flesch's published bands, with the fiction target zone
    (60-80) marked. There is deliberately no "readable threshold" line: 60 is
    not a pass mark, and drawing it as one would say the opposite of what the
    report says. It would also mislead in a second way — the aim is a *zone*,
    so a chapter at 88 clears any 60 line while still sitting above target.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))

    for floor, ceiling, colour, _ in FLESCH_BANDS:
        ax.axhspan(floor, ceiling, color=colour, zorder=0)

    aim_low, aim_high = 60, 80
    ax.axhspan(aim_low, aim_high, facecolor="none", edgecolor="#90a4ae",
               linestyle="--", linewidth=0.9, zorder=2,
               label=f"aim for fiction ({aim_low}-{aim_high})")

    ax.plot(df["order"], df["flesch"], marker="o", linewidth=1.6,
            color="#37474f", zorder=3)

    ax.set_title("Pacing curve (Flesch Reading Ease)")
    ax.set_xlabel("Chapter order")
    ax.set_ylabel("Flesch score")

    low = max(0, df["flesch"].min() - 15)
    high = min(105, df["flesch"].max() + 15)
    ax.set_ylim(low, high)
    ax.grid(axis="y", alpha=0.25, zorder=1)

    # Chapters are whole numbers; matplotlib would otherwise offer 0.5, 1.5, …
    ax.set_xticks(list(df["order"]))

    # Band names inside the axes, and only the ones actually visible:
    # x in axes fraction, y in data coordinates.
    for floor, ceiling, _, name in FLESCH_BANDS:
        middle = (max(floor, low) + min(ceiling, high)) / 2
        if not (low < middle < high) or min(ceiling, high) - max(floor, low) <= 4:
            continue
        # nudge clear of the target-zone bounds, which a midpoint can land on
        for bound in (aim_low, aim_high):
            if abs(middle - bound) < 2:
                middle = bound + 3.5
        ax.text(0.995, middle, name, transform=ax.get_yaxis_transform(),
                fontsize=7, color="#90a4ae", va="center", ha="right", zorder=4)

    ax.legend(fontsize=8, loc="lower left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return Path(output_path)


# -----------------------------------------------
# matplotlib cache — call once at import time
# so every script that imports read_stats gets it set
# -----------------------------------------------

_cache_dir = (Path(__file__).parent / ".matplotlib_cache").resolve()
_cache_dir.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_dir))
