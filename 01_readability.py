import os
import re
from pathlib import Path

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


# -------------------------------
# Recursive directory walker
# -------------------------------
def analyze_directory(path="."):
    results = []
    base = Path(path)

    for md_file in base.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        plain = strip_markdown(content)
        metrics = readability_metrics(plain)
        if metrics:
            results.append((md_file, metrics))

    return results


# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    folder = "."  # change to your docs directory
    stats = analyze_directory("/Users/flofonic/Documents/Blackout/blackout/manuscript/")

    print(f"Readability results for markdown files in: {folder}\n")

    for path, m in stats:
        print(f"--- {path} ---")
        print(f"Words:          {m['words']}")
        print(f"Sentences:      {m['sentences']}")
        print(f"Syllables:      {m['syllables']}")
        print(f"Flesch:         {m['flesch']:.2f}")
        print(f"FK Grade:       {m['fk_grade']:.2f}")
        print(f"Gunning Fog:    {m['gunning_fog']:.2f}")
        print()



    # ----------------------------------
    # Summary table sorted by difficulty
    # Hardest = lowest Flesch score
    # ----------------------------------
    print("\n=== Summary (sorted by difficulty: hardest → easiest) ===\n")

    stats_sorted = sorted(stats, key=lambda x: x[1]["flesch"])

    print(f"{'Flesch':>7}  {'FK':>5}  {'Fog':>5}  {'Words':>6}  File")
    print("-" * 70)

    for path, m in stats_sorted:
        print(f"{m['flesch']:7.2f}  {m['fk_grade']:5.2f}  {m['gunning_fog']:5.2f}  "
              f"{m['words']:6d}  {path}")



