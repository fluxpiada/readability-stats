"""
05_lexical_div.py — TTR and MTLD lexical diversity per chapter.
Usage: python 05_lexical_div.py [folder]
"""

import sys
from read_stats import (
    METRICS, clean_tokens, ensure_nltk_data, legend, load_chapters, mtld, ttr,
)

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def main(folder: str = MANUSCRIPT) -> None:
    if not ensure_nltk_data():
        print("NLTK punkt/stopwords data unavailable — cannot measure lexical diversity.")
        return

    ttr_h = f"TTR {METRICS['ttr'].symbol}"
    mtld_h = f"MTLD {METRICS['mtld'].symbol}"
    print(f"{'Chapter':<40} {ttr_h:>8}  {mtld_h:>9}")
    print("-" * 60)
    for filename, text in load_chapters(folder):
        tokens = clean_tokens(text)
        print(f"{filename:<40} {ttr(tokens):8.3f}  {mtld(tokens):9.2f}")

    print()
    print(legend(["ttr", "mtld"]))


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
