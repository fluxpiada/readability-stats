"""
06_complex_deltas.py — chapter-to-chapter changes in Flesch, Fog, and word count.
Usage: python 06_complex_deltas.py [folder]
"""

from read_stats import chapter_frame, legend, resolve_folder


def main(folder: str) -> None:
    df, _ = chapter_frame(folder)

    print(df[["chapter", "delta_flesch", "delta_fog", "delta_words"]].to_string(index=False))
    print()
    print(legend(["delta"]))


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
