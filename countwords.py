"""
countwords.py — total word count across all .md and .docx files in a folder.
Usage: python countwords.py [folder]
"""

from read_stats import count_words, load_chapters, resolve_folder


def main(folder: str) -> None:
    chapters = load_chapters(folder)
    total = 0
    for filename, text in chapters:
        words = count_words(text)
        if words:
            total += words
            print(f"{words:>7}  {filename}")
    print("-" * 40)
    print(f"{total:>7}  TOTAL")


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
