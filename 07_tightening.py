"""
07_tightening.py — rank chapters by how much they need tightening.
High score = wordy, dense, long sentences, low readability.
Usage: python 07_tightening.py [folder]
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

    df["tightening_score"] = (
        df["fog"] * 0.5
        + df["fk"] * 0.3
        + df["words"] * 0.0005
        + (df["flesch"].max() - df["flesch"]) * 0.3
    )

    result = df.sort_values("tightening_score", ascending=False)[
        ["chapter", "tightening_score", "flesch", "fog", "fk", "words"]
    ]

    print("=== Chapters ranked by tightening need (highest priority first) ===\n")
    print(result.to_string(index=False))


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    main(folder)
