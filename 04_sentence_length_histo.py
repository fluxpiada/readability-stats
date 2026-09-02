"""
04_sentence_length_histo.py — histogram of sentence lengths per chapter.
Usage: python 04_sentence_length_histo.py [folder]
"""

from pathlib import Path

# read_stats first: importing it sets MPLCONFIGDIR, which matplotlib reads at
# its own import time, so the order here is load-bearing.
from read_stats import ensure_nltk_data, load_chapters, resolve_folder

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sentence_lengths(text: str) -> list[int]:
    import nltk

    # preserve_line stops word_tokenize running the sentence tokenizer again
    # over a string that has already been split into one sentence.
    return [len(nltk.word_tokenize(s, preserve_line=True))
            for s in nltk.sent_tokenize(text)]


def plot_histograms(folder: str) -> None:
    if not ensure_nltk_data():
        print("NLTK punkt data unavailable — cannot measure sentence lengths.")
        return

    chapters = load_chapters(folder)
    output_dir = Path("sentence_histograms")
    output_dir.mkdir(exist_ok=True)

    for filename, text in chapters:
        lengths = sentence_lengths(text)
        if not lengths:
            continue

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(lengths, bins=25, color="steelblue", edgecolor="white")
        ax.set_title(f"Sentence Lengths: {filename}")
        ax.set_xlabel("Words per sentence")
        ax.set_ylabel("Count")
        plt.tight_layout()

        out_file = output_dir / Path(filename).with_suffix(".png")
        plt.savefig(out_file, dpi=120)
        plt.close()
        print(f"Saved: {out_file}")


if __name__ == "__main__":
    folder = resolve_folder()
    plot_histograms(folder)
