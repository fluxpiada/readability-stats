"""
06_complex_deltas.py — chapter-to-chapter changes in Flesch, Fog, and word count.
Usage: python 06_complex_deltas.py [folder]
"""

import sys
import pandas as pd
from utils import load_chapters, readability_metrics

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"


def build_dataframe(folder: str) -> pd.DataFrame:
    rows = []
    for i, (filename, text) in enumerate(load_chapters(folder)):
        m = readability_metrics(text)
        if m:
            rows.append({
                "chapter": filename,
                "order":   i,
                "flesch":  m["flesch"],
                "fk":      m["fk_grade"],
                "fog":     m["gunning_fog"],
                "words":   m["words"],
            })
    return pd.DataFrame(rows)


def main(folder: str = MANUSCRIPT) -> None:
    df = build_dataframe(folder)

    df["delta_flesch"] = df["flesch"].diff()
    df["delta_fog"]    = df["fog"].diff()
    df["delta_words"]  = df["words"].diff()

    print(df[["chapter", "delta_flesch", "delta_fog", "delta_words"]].to_string(index=False))


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
