"""
05_lexical_div.py — TTR and MTLD lexical diversity per chapter.
Usage: python 05_lexical_div.py [folder]
"""

from read_stats import (
    clean_tokens, ensure_nltk_data, header, legend, load_chapters, mtld,
    resolve_folder, ttr,
)


def main(folder: str) -> None:
    if not ensure_nltk_data():
        print("NLTK punkt/stopwords data unavailable — cannot measure lexical diversity.")
        return

    ttr_h, mtld_h = header("ttr"), header("mtld")
    print(f"{'Chapter':<40} {ttr_h:>8}  {mtld_h:>9}")
    print("-" * 60)
    for filename, text in load_chapters(folder):
        tokens = clean_tokens(text)
        print(f"{filename:<40} {ttr(tokens):8.3f}  {mtld(tokens):9.2f}")

    print()
    print(legend(["ttr", "mtld"]))


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
