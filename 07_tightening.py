"""
07_tightening.py — rank chapters by how much they need tightening.
High score = wordy, dense, long sentences, low readability.
Usage: python 07_tightening.py [folder]
"""

import pandas as pd
from read_stats import legend, load_chapters, readability_metrics, resolve_folder, tightening_score


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


def main(folder: str) -> None:
    df = build_dataframe(folder)

    df["tightening_score"] = tightening_score(df)

    result = df.sort_values("tightening_score", ascending=False)[
        ["chapter", "tightening_score", "flesch", "fog", "fk", "words"]
    ]

    print("=== Chapters ranked by tightening need (highest priority first) ===\n")
    print(result.to_string(index=False))
    print()
    print(legend(["tightening", "flesch", "fog", "fk"]))


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
