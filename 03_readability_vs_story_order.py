"""
03_readability_vs_story_order.py — plot Flesch score across chapter order (pacing curve).
Usage: python 03_readability_vs_story_order.py [folder]
"""

import sys
import pandas as pd
from read_stats import load_chapters, plot_pacing_curve, readability_metrics  # also sets MPLCONFIGDIR

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def build_dataframe(folder: str) -> pd.DataFrame:
    rows = []
    for i, (filename, text) in enumerate(load_chapters(folder)):
        m = readability_metrics(text)
        if m:
            rows.append({
                "chapter":  filename,
                "order":    i,
                "flesch":   m["flesch"],
                "fk":       m["fk_grade"],
                "fog":      m["gunning_fog"],
                "words":    m["words"],
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    df = build_dataframe(folder)
    written = plot_pacing_curve(df)
    print(f"Saved: {written.resolve()}")
