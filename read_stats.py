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
# matplotlib cache — call once at import time
# so every script that imports utils gets it set
# -----------------------------------------------

_cache_dir = (Path(__file__).parent / ".matplotlib_cache").resolve()
_cache_dir.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_dir))
