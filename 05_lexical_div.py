# 6. Lexical Diversity (TTR + MTLD)
#TTR (type-token ratio) is naive; MTLD is better.


from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

stop = set(stopwords.words("english"))

def clean_tokens(text):
    toks = [w.lower() for w in word_tokenize(text)]
    return [t for t in toks if t not in stop and t not in string.punctuation]

def ttr(tokens):
    return len(set(tokens)) / len(tokens)

def mtld(tokens, threshold=0.72):
    factors, segment = 0, []
    for t in tokens:
        segment.append(t)
        if (len(set(segment)) / len(segment)) < threshold:
            factors += 1
            segment = []
    if segment:
        factors += (len(segment) / (len(set(segment)) / threshold))
    return len(tokens) / factors

for chapter, text in chapters:
    toks = clean_tokens(text)
    print(chapter, "TTR:", ttr(toks), "MTLD:", mtld(toks))
