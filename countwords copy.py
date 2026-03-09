"""
countwords.py — total word count across all .md files in a folder.
Usage: python countwords.py [folder]
"""

import sys
from utils import load_chapters, readability_metrics

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def main(folder: str = MANUSCRIPT) -> None:
    chapters = load_chapters(folder)
    total = 0
    for filename, text in chapters:
        m = readability_metrics(text)
        if m:
            total += m["words"]
            print(f"{m['words']:>7}  {filename}")
    print("-" * 40)
    print(f"{total:>7}  TOTAL")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
