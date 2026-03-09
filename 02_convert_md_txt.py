from pathlib import Path
import re

# 3. Convert Markdown → plain text
# Reuse your existing strip_markdown() function.


def strip_markdown(md):
    text = md

    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)

    # Remove images ![alt](url)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Remove links [text](url)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

    # Remove headings, lists, blockquotes markers
    text = re.sub(r"(^|\n)[#>\-\*\+]+\s*", r"\1", text)

    # Remove emphasis markers ** __ * _
    text = re.sub(r"[*_]{1,3}", "", text)

    return text


def load_chapters(folder="/Users/flofonic/Documents/Blackout/blackout/manuscript"):
    chapters = []

    for path in sorted(Path(folder).rglob("*.md")):
        # Skip anything in a folder named 'draft'
        if "draft" in path.parts:
            continue

        with open(path, "r", encoding="utf-8") as f:
            raw_markdown = f.read()

        plain_text = strip_markdown(raw_markdown)

        chapters.append((path.name, plain_text))

    return chapters


def write_plaintext_chapters(output_dir="converted_txt", folder="/Users/flofonic/Documents/Blackout/blackout/manuscript"):
    """Convert all markdown chapters to .txt files for quick reading/analysis."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for name, text in load_chapters(folder):
        txt_name = Path(name).with_suffix(".txt")
        (out_path / txt_name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    write_plaintext_chapters()
