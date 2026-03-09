"""
01_readability.py — print readability metrics for every chapter, sorted by difficulty.
Usage: python 01_readability.py [folder]
"""

import sys
from utils import load_chapters, readability_metrics

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def main(folder: str = MANUSCRIPT) -> None:
    stats = []
    for filename, text in load_chapters(folder):
        m = readability_metrics(text)
        if m:
            stats.append((filename, m))

    if not stats:
        print("No .md files found.")
        return

    print(f"Readability results for: {folder}\n")
    for filename, m in stats:
        print(f"--- {filename} ---")
        print(f"  Words:        {m['words']}")
        print(f"  Sentences:    {m['sentences']}")
        print(f"  Flesch:       {m['flesch']:.2f}")
        print(f"  FK Grade:     {m['fk_grade']:.2f}")
        print(f"  Gunning Fog:  {m['gunning_fog']:.2f}")
        print()

    print("\n=== Summary (hardest → easiest by Flesch) ===\n")
    stats_sorted = sorted(stats, key=lambda x: x[1]["flesch"])
    print(f"{'Flesch':>7}  {'FK':>5}  {'Fog':>5}  {'Words':>6}  File")
    print("-" * 70)
    for filename, m in stats_sorted:
        print(f"{m['flesch']:7.2f}  {m['fk_grade']:5.2f}  {m['gunning_fog']:5.2f}  {m['words']:6d}  {filename}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
