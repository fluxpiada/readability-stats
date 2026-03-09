# 8. “Which Chapter Most Needs Tightening”
# A practical formula:  High score = → too wordy → too dense → long sentences → low Flesch
# This ranking gives you an actionable edit list.


    df["tightening_score"] = (
    df["fog"] * 0.5 +
    df["fk"] * 0.3 +
    df["words"] * 0.0005 +
    (df["flesch"].max() - df["flesch"]) * 0.3
)

df.sort_values("tightening_score", ascending=False)[
    ["chapter", "tightening_score", "flesh", "fog", "fk", "words"]
].head()
