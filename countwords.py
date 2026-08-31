"""
countwords.py — total word count across all .md and .docx files in a folder.
Usage: python countwords.py [folder]
"""

from read_stats import load_chapters, readability_metrics, resolve_folder


def main(folder: str) -> None:
    chapters = load_chapters(folder)
    total = 0
    for filename, text in chapters:
        m = readability_metrics(text)
        if m:
            total += m["words"]
            print(f"{m['words']:>7}  {filename}")
    print("-" * 40)
    print(f"{total:>7}  TOTAL")


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
