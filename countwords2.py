# Write your code here :-)
import os
import re

def count_words_in_markdown_folder(folder_path):
    total_words = 0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".md"):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            # Strip markdown symbols (very basic but effective)
            text = re.sub(r"[#>*_`~\[\]\(\)!-]", " ", text)

            # Count real words
            words = re.findall(r"\b\w+\b", text)
            total_words += len(words)

    return total_words


# Example usage:
folder = "/Users/flofonic/Documents/Blackout/blackout/content/manuscript"
print("Total words:", count_words_in_markdown_folder(folder))
