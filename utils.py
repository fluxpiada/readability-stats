"""
utils.py — shared helpers for readability-stats
"""

import os
import re
from pathlib import Path


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
# Chapter loader
# -----------------------------------------------

def load_chapters(folder: str) -> list[tuple[str, str]]:
    """
    Recursively load all .md files under *folder*, skipping any path
    that contains a component named 'draft'.
    Returns a sorted list of (filename, plain_text) tuples.
    """
    chapters = []
    for path in sorted(Path(folder).rglob("*.md")):
        if "draft" in path.parts:
            continue
        raw = path.read_text(encoding="utf-8")
        chapters.append((path.name, strip_markdown(raw)))
    return chapters


# -----------------------------------------------
# matplotlib cache — call once at import time
# so every script that imports utils gets it set
# -----------------------------------------------

_cache_dir = (Path(__file__).parent / ".matplotlib_cache").resolve()
_cache_dir.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_dir))
