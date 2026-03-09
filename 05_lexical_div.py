"""
05_lexical_div.py — TTR and MTLD lexical diversity per chapter.
Usage: python 05_lexical_div.py [folder]
"""

import sys
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from utils import load_chapters

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"

nltk.download("punkt",       quiet=True)
nltk.download("punkt_tab",   quiet=True)
nltk.download("stopwords",   quiet=True)


def clean_tokens(text: str) -> list[str]:
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


def main(folder: str = MANUSCRIPT) -> None:
    print(f"{'Chapter':<40} {'TTR':>6}  {'MTLD':>7}")
    print("-" * 58)
    for filename, text in load_chapters(folder):
        tokens = clean_tokens(text)
        print(f"{filename:<40} {ttr(tokens):6.3f}  {mtld(tokens):7.2f}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
