"""
utils.py — shared helpers for readability-stats
"""

import os
import re
import sys
from pathlib import Path

try:
    import docx  # python-docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


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

def resolve_folder(default: str | None = None) -> str:
    """
    Return the folder to analyse, in this priority order:
      1. CLI argument (sys.argv[1]) if provided
      2. Interactive prompt if running in a terminal
      3. *default* if supplied and no input given
    Raises SystemExit if nothing is available.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]

    if sys.stdin.isatty():
        prompt = "Folder to analyse"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        answer = input(prompt).strip()
        if answer:
            return answer

    if default:
        return default

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

def readability_metrics(text: str) -> dict | None:
    words = re.findall(r"\b[\w']+\b", text)
    word_count = len(words)

    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_count = len(sentences)

    if sentence_count == 0 or word_count == 0:
        return None

    syllable_count = sum(count_syllables(w) for w in words)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)

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
    """Extract plain text from a .docx file (requires python-docx)."""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx is not installed. Run: pip install python-docx")
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
        if path.suffix.lower() == ".md":
            raw = path.read_text(encoding="utf-8")
            text = strip_markdown(raw)
        elif path.suffix.lower() == ".docx":
            try:
                text = extract_docx(path)
            except ImportError as e:
                print(f"Skipping {path.name}: {e}")
                continue
        else:
            continue

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

            for package in ("punkt", "punkt_tab", "stopwords"):
                nltk.download(package, quiet=True)
            stopwords.words("english")   # forces a real lookup, so missing data fails here
            _NLTK_READY = True
        except Exception:
            _NLTK_READY = False
    return _NLTK_READY


def clean_tokens(text: str) -> list[str]:
    """Lowercased word tokens, minus stopwords and punctuation."""
    import string
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords

    stop = set(stopwords.words("english"))
    tokens = [w.lower() for w in word_tokenize(text)]
    return [t for t in tokens if t not in stop and t not in string.punctuation]


def ttr(tokens: list[str]) -> float:
    """Type-token ratio — naive but fast."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def mtld(tokens: list[str], threshold: float = 0.72) -> float:
    """Measure of Textual Lexical Diversity."""
    if not tokens:
        return 0.0

    factors, segment = 0, []
    for t in tokens:
        segment.append(t)
        if (len(set(segment)) / len(segment)) < threshold:
            factors += 1
            segment = []

    if segment:
        factors += (len(segment) / (len(set(segment)) / threshold))

    return len(tokens) / factors if factors else 0.0


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
# Pacing curve plot
# -----------------------------------------------

def plot_pacing_curve(df, output_path: str = "pacing_curve.png") -> Path:
    """Plot Flesch score against chapter order. Returns the written path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["order"], df["flesch"], marker="o", linewidth=1.5)
    ax.axhline(60, color="gray", linestyle="--", linewidth=0.8, label="Readable threshold (60)")
    ax.set_title("Pacing Curve (Flesch Reading Ease)")
    ax.set_xlabel("Chapter order")
    ax.set_ylabel("Flesch score")
    ax.legend()
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
