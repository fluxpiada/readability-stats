"""
04_sentence_length_histo.py — histogram of sentence lengths per chapter.
Usage: python 04_sentence_length_histo.py [folder]
"""

import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nltk
from pathlib import Path
from utils import load_chapters  # also sets MPLCONFIGDIR

MANUSCRIPT = "/Users/flofonic/Documents/Blackout/blackout/manuscript"

# Download punkt tokenizer if not already present
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)


def sentence_lengths(text: str) -> list[int]:
    sentences = nltk.sent_tokenize(text)
    return [len(nltk.word_tokenize(s)) for s in sentences]


def plot_histograms(folder: str) -> None:
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
    folder = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    plot_histograms(folder)
