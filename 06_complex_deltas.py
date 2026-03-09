# 7. Complexity Deltas (chapter-to-chapter trend)
# Compute change between consecutive chapters:
# This tells you: where complexity spikes, where pacing slows, where readability jumps suddenly



df["delta_flesch"] = df["flesch"].diff()
df["delta_fog"] = df["fog"].diff()
df["delta_words"] = df["words"].diff()

print(df[["chapter", "delta_flesch", "delta_fog", "delta_words"]])
