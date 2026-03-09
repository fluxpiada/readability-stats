"""
03_readability_vs_story_order.py — plot Flesch score across chapter order (pacing curve).
Usage: python 03_readability_vs_story_order.py [folder]
"""

import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from utils import load_chapters, readability_metrics  # also sets MPLCONFIGDIR

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


def plot_pacing_curve(df: pd.DataFrame, output_path: str = "pacing_curve.png") -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["order"], df["flesch"], marker="o", linewidth=1.5)
    ax.axhline(60, color="gray", linestyle="--", linewidth=0.8, label="Readable threshold (60)")
    ax.set_title("Pacing Curve (Flesch Reading Ease)")
    ax.set_xlabel("Chapter order")
    ax.set_ylabel("Flesch score")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved: {Path(output_path).resolve()}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    df = build_dataframe(folder)
    plot_pacing_curve(df)
