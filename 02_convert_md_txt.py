"""
02_convert_md_txt.py — convert all manuscript .md files to plain .txt.
Usage: python 02_convert_md_txt.py [folder] [output_dir]
"""

import sys
from pathlib import Path
from utils import load_chapters

MANUSCRIPT  = "/Users/flofonic/Documents/Blackout/blackout/manuscript"
OUTPUT_DIR  = "converted_txt"


def write_plaintext_chapters(folder: str = MANUSCRIPT, output_dir: str = OUTPUT_DIR) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    chapters = load_chapters(folder)
    for filename, text in chapters:
        txt_name = Path(filename).with_suffix(".txt")
        (out / txt_name).write_text(text, encoding="utf-8")
        print(f"Written: {out / txt_name}")

    print(f"\n{len(chapters)} files converted → {out.resolve()}")


if __name__ == "__main__":
    folder     = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    output_dir = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_DIR
    write_plaintext_chapters(folder, output_dir)
