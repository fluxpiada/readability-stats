"""
07_tightening.py — rank chapters by how much they need tightening.
High score = wordy, dense, long sentences, low readability.
Usage: python 07_tightening.py [folder]
"""

from read_stats import chapter_frame, legend, resolve_folder


def main(folder: str) -> None:
    df, _ = chapter_frame(folder)

    result = df.sort_values("tightening", ascending=False)[
        ["chapter", "tightening", "flesch", "fog", "fk", "words"]
    ].rename(columns={"tightening": "tightening_score"})

    print("=== Chapters ranked by tightening need (highest priority first) ===\n")
    print(result.to_string(index=False))
    print()
    print(legend(["tightening", "flesch", "fog", "fk"]))


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
