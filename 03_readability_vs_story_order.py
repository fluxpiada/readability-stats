#4. Pacing Curve (Readability vs Story Order)
#You already compute Flesch/FK/Fog.
#Now put them in a DataFrame and plot them.
import os
import re
from pathlib import Path

cache_dir = (Path(__file__).parent / ".matplotlib_cache").resolve()
cache_dir.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import pandas as pd

# -------------------------------
# Markdown → plain text stripper
# -------------------------------
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


# -------------------------------
# Readability helpers
# -------------------------------
def count_syllables(word):
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word)
    vowels = "aeiouy"
    if not word:
        return 0

    syllables = 0
    prev_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            syllables += 1
        prev_vowel = is_vowel

    # silent e
    if word.endswith("e") and syllables > 1:
        syllables -= 1

    return max(1, syllables)


def readability_metrics(text):
    words = re.findall(r"\b[\w']+\b", text)
    word_count = len(words)

    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]
    sentence_count = len(sentences)

    syllable_count = sum(count_syllables(w) for w in words)

    if sentence_count == 0 or word_count == 0:
        return None

    # Flesch Reading Ease
    flesch = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)

    # Flesch-Kincaid Grade
    fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59

    # Gunning Fog
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)
    fog = 0.4 * ((word_count / sentence_count) + 100 * (complex_words / word_count))

    return {
        "words": word_count,
        "sentences": sentence_count,
        "syllables": syllable_count,
        "flesch": flesch,
        "fk_grade": fk_grade,
        "gunning_fog": fog,
    }

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


chapters = load_chapters()

rows = []
for i, (name, text) in enumerate(chapters):
    m = readability_metrics(text)
    rows.append({
        "chapter": name,
        "order": i,
        "flesch": m["flesch"],
        "fk": m["fk_grade"],
        "fog": m["gunning_fog"],
        "words": m["words"],
    })

df = pd.DataFrame(rows)

plt.plot(df["order"], df["flesch"])
plt.title("Pacing Curve (Flesch Reading Ease)")
plt.xlabel("Chapter order")
plt.ylabel("Flesch score")
output_path = Path("pacing_curve.png")
plt.tight_layout()
plt.savefig(output_path)
print(f"Saved plot to {output_path.resolve()}")
