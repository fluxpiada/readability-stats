#5. Sentence-Length Histograms

import numpy as np
import matplotlib.pyplot as plt
import nltk

def sentence_lengths(text):
    sents = nltk.sent_tokenize(text)
    words = [len(nltk.word_tokenize(s)) for s in sents]
    return words

for chapter, text in chapters:
    lengths = sentence_lengths(text)
    plt.hist(lengths, bins=25)
    plt.title(f"Sentence Lengths: {chapter}")
    plt.xlabel("Words per sentence")
    plt.ylabel("Count")
    plt.show()
