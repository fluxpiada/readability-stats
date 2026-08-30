"""
05_lexical_div.py — TTR and MTLD lexical diversity per chapter.
Usage: python 05_lexical_div.py [folder]
"""

import sys
from read_stats import clean_tokens, ensure_nltk_data, load_chapters, mtld, ttr

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def main(folder: str = MANUSCRIPT) -> None:
    if not ensure_nltk_data():
        print("NLTK punkt/stopwords data unavailable — cannot measure lexical diversity.")
        return

    print(f"{'Chapter':<40} {'TTR':>6}  {'MTLD':>7}")
    print("-" * 58)
    for filename, text in load_chapters(folder):
        tokens = clean_tokens(text)
        print(f"{filename:<40} {ttr(tokens):6.3f}  {mtld(tokens):7.2f}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
