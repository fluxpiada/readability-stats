"""
08_report.py — one combined report of every statistic, as report.md and report.pdf.
Usage: python 08_report.py [folder] [output_dir]

Both files are written from the same DataFrame, so they cannot drift apart.

With no output_dir, each run is snapshotted into reports/<timestamp>/ and never
overwrites an earlier one, so you can watch the manuscript change across drafts.
Passing an output_dir writes the three files straight into it instead.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from read_stats import (
    clean_tokens,
    ensure_nltk_data,
    header,
    legend,
    load_chapters,
    mtld,
    plot_pacing_curve,
    range_note,
    readability_metrics,
    register_unicode_font,
    tightening_score,
    ttr,
)

MANUSCRIPT  = "/Users/flofonic/Documents/Blackout/blackout/manuscript"
REPORTS_DIR = "reports"

# Publishing conventions for the page estimate.
WORDS_PER_MANUSCRIPT_PAGE = 250   # double-spaced, 12pt, 1" margins
WORDS_PER_PAPERBACK_PAGE  = 300   # typeset trade paperback


# -----------------------------------------------
# The explanations, kept in one place so the
# markdown and the PDF always say the same thing
# -----------------------------------------------

# Each entry is (metric key, term, explanation). The key pulls the range,
# direction and target out of read_stats.METRICS, so the glossary and the table
# headers can never disagree about which way is up. None means the entry has no
# column of its own (the chart, for instance).
GLOSSARY = [
    ("flesch", "Flesch Reading Ease",
     "A 0–100 score built from average sentence length and average syllables per word. "
     "Higher is easier. 90–100 is very easy, 60–70 is plain English and where most popular "
     "fiction sits, 30–50 is dense (academic or heavily subordinated prose), and below 30 is "
     "very hard going. Scores can fall outside 0–100 in short or extreme passages."),

    ("fk", "Flesch–Kincaid Grade",
     "The same inputs as Flesch, recast as a US school grade level. 8.0 means an average "
     "eighth-grader could follow it. Most commercial fiction lands between 5 and 9."),

    ("fog", "Gunning Fog",
     "Combines sentence length with the share of complex words (three or more syllables). It "
     "is sensitive to jargon and abstraction in a way Flesch is not. Also roughly a grade "
     "level: under 12 is comfortable for a general reader."),

    ("avg_sent", "Average sentence length",
     "Words divided by sentences. Useful next to the readability scores, because a chapter can "
     "score badly either from long sentences or from long words, and this separates the two."),

    ("ttr", "TTR (type-token ratio)",
     "Unique words divided by total words, after stopwords and punctuation are removed. Simple, "
     "but it falls automatically as a chapter gets longer, so only compare chapters of similar "
     "length — otherwise you are measuring word count, not vocabulary."),

    ("mtld", "MTLD",
     "Measure of Textual Lexical Diversity — vocabulary variety corrected for length. This is "
     "the number to trust when your chapters differ in size. Low diversity can mean a tight, "
     "controlled voice, or it can mean an unnoticed tic word."),

    ("delta", "Chapter-to-chapter deltas",
     "How far readability, fog and word count jump between consecutive chapters. Large swings "
     "are where the reading experience changes gear. Sometimes that is deliberate pacing; "
     "sometimes it is a chapter written on a different day in a different register."),

    (None, "Pacing curve",
     "Flesch plotted against chapter order, over Flesch's interpretation bands, with the "
     "fiction target zone (60-80) outlined. Dips are the dense stretches. Long flat runs are "
     "where the texture stops changing. Leaving the zone is not a fault — it is a question."),

    ("tightening", "Tightening score",
     "A composite ranking that pushes chapters which are simultaneously wordy, dense and "
     "low-readability to the top. It is a triage list for revision, nothing more: re-read the "
     "top few chapters before you decide anything."),
]

CAVEAT = (
    "These are surface measurements — sentence length, syllable counts, word variety. They say "
    "how much effort a page takes to process, not whether it is any good. Plot, character, "
    "tension and dialogue quality are invisible to all of them. Deliberately difficult prose "
    "scores badly here, and short flat sentences score well even when they are dull. Every "
    "index above rewards brevity, so do not optimise for the numbers — read the chapters they "
    "point you at. No language model is involved: every figure is arithmetic over the text."
)


# -----------------------------------------------
# Data
# -----------------------------------------------

def build_dataframe(folder: str) -> tuple[pd.DataFrame, bool]:
    """Return (per-chapter stats, whether lexical diversity could be measured)."""
    lexical = ensure_nltk_data()
    rows = []

    for i, (filename, text) in enumerate(load_chapters(folder)):
        m = readability_metrics(text)
        if not m:
            continue

        row = {
            "chapter":   filename,
            "order":     i,
            "words":     m["words"],
            "sentences": m["sentences"],
            "avg_sent":  m["words"] / m["sentences"],
            "flesch":    m["flesch"],
            "fk":        m["fk_grade"],
            "fog":       m["gunning_fog"],
        }

        if lexical:
            tokens = clean_tokens(text)
            row["ttr"]  = ttr(tokens)
            row["mtld"] = mtld(tokens)

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df, lexical

    df["delta_flesch"] = df["flesch"].diff()
    df["delta_fog"]    = df["fog"].diff()
    df["delta_words"]  = df["words"].diff()
    df["tightening"]   = tightening_score(df)
    return df, lexical


def fmt(value, decimals: int = 1) -> str:
    """Format a number for a table cell; blank for missing values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if decimals == 0:
        return f"{int(round(value)):,}"
    return f"{value:,.{decimals}f}"


def table_data(df: pd.DataFrame, lexical: bool) -> dict[str, tuple[list[str], list[list[str]]]]:
    """Build every table once, as (headers, rows) of preformatted strings."""
    # Headers are shared by both writers and stay short enough not to wrap in
    # the PDF's narrow numeric columns. They may now use the direction arrows:
    # write_pdf registers DejaVuSans, so glyphs outside WinAnsi survive.
    per_chapter_headers = ["Chapter", "Words", "Sents",
                           header("avg_sent"), header("flesch"),
                           header("fk"), header("fog")]
    if lexical:
        per_chapter_headers += [header("ttr"), header("mtld")]

    per_chapter = []
    for _, r in df.iterrows():
        row = [r["chapter"], fmt(r["words"], 0), fmt(r["sentences"], 0),
               fmt(r["avg_sent"]), fmt(r["flesch"]), fmt(r["fk"]), fmt(r["fog"])]
        if lexical:
            row += [fmt(r["ttr"], 3), fmt(r["mtld"], 1)]
        per_chapter.append(row)

    hardest = [
        [r["chapter"], fmt(r["flesch"]), fmt(r["fk"]), fmt(r["fog"]), fmt(r["words"], 0)]
        for _, r in df.sort_values("flesch").iterrows()
    ]

    tightening = [
        [r["chapter"], fmt(r["tightening"]), fmt(r["flesch"]), fmt(r["fog"]), fmt(r["words"], 0)]
        for _, r in df.sort_values("tightening", ascending=False).iterrows()
    ]

    deltas = [
        [r["chapter"], fmt(r["delta_flesch"]), fmt(r["delta_fog"]), fmt(r["delta_words"], 0)]
        for _, r in df.iterrows()
    ]

    return {
        "per_chapter": (per_chapter_headers, per_chapter),
        "hardest":     (["Chapter", header("flesch"), header("fk"),
                         header("fog"), "Words"], hardest),
        "tightening":  (["Chapter", header("tightening"), header("flesch"),
                         header("fog"), "Words"], tightening),
        "deltas":      (["Chapter", header("delta", "Flesch change"),
                         header("delta", "Fog change"),
                         header("delta", "Words change")], deltas),
    }


# Which metric columns each table shows, so the legend under it matches.
TABLE_KEYS = {
    "per_chapter": ["avg_sent", "flesch", "fk", "fog", "ttr", "mtld"],
    "hardest":     ["flesch", "fk", "fog"],
    "tightening":  ["tightening", "flesch", "fog"],
    "deltas":      ["delta"],
}


def table_legend(key: str, lexical: bool = True) -> str:
    """The legend line under the table with this key."""
    keys = TABLE_KEYS.get(key, [])
    if not lexical:
        keys = [k for k in keys if k not in ("ttr", "mtld")]
    return legend(keys)


def summary_lines(df: pd.DataFrame, folder: str) -> list[tuple[str, str]]:
    total_words = int(df["words"].sum())
    return [
        ("Source folder",     folder),
        ("Generated",         date.today().isoformat()),
        ("Chapters",          f"{len(df):,}"),
        ("Total words",       f"{total_words:,}"),
        ("Manuscript pages",  f"~{round(total_words / WORDS_PER_MANUSCRIPT_PAGE):,} "
                              f"(at {WORDS_PER_MANUSCRIPT_PAGE} words/page, double-spaced)"),
        ("Paperback pages",   f"~{round(total_words / WORDS_PER_PAPERBACK_PAGE):,} "
                              f"(at {WORDS_PER_PAPERBACK_PAGE} words/page, typeset)"),
        ("Mean Flesch",       f"{df['flesch'].mean():.1f}"),
        ("Hardest chapter",   str(df.loc[df['flesch'].idxmin(), 'chapter'])),
        ("Easiest chapter",   str(df.loc[df['flesch'].idxmax(), 'chapter'])),
    ]


# -----------------------------------------------
# Section text — shared by both writers
# -----------------------------------------------

SECTIONS = [
    ("per_chapter", "Every chapter",
     "All metrics in story order. Skim the Flesch column for outliers. "
     "Sents is the sentence count; Avg len is the average words per sentence."),
    ("hardest", "Hardest to easiest",
     "The same chapters ranked by Flesch Reading Ease, lowest (densest) first."),
    ("tightening", "Tightening priority",
     "Chapters that are wordy, dense and hard to read at the same time. A revision triage list."),
    ("deltas", "Chapter-to-chapter change",
     "How sharply each chapter differs from the one before it. Big jumps change the reading gear."),
]


# -----------------------------------------------
# Markdown writer
# -----------------------------------------------

def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Small markdown table builder — avoids a tabulate dependency for one function."""
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(cells) + " |" for cells in rows]
    return "\n".join(out)


def write_markdown(df, lexical, tables, folder, out_dir, chart_name) -> Path:
    parts = ["# Readability report", ""]

    for label, value in summary_lines(df, folder):
        parts.append(f"- **{label}:** {value}")
    parts.append("")

    if not lexical:
        parts += ["> NLTK's punkt/stopwords data could not be downloaded, so the TTR and MTLD "
                  "columns are omitted from this report. Everything else is unaffected.", ""]

    for key, title, blurb in SECTIONS:
        headers, rows = tables[key]
        parts += [f"## {title}", "", blurb, "", md_table(headers, rows), ""]
        note = table_legend(key, lexical)
        if note:
            parts += ["*" + note.replace("\n", "*  \n*") + "*", ""]

    parts += ["## Pacing curve", "",
              "Flesch score across chapter order. The shaded bands are Flesch's own; the "
              "dashed outline is the 60-80 target zone for fiction.",
              "", f"![Pacing curve]({chart_name})", ""]

    parts += ["## What each statistic means", ""]
    for key, term, explanation in GLOSSARY:
        parts += [f"**{term}** — {explanation}", ""]
        note = range_note(key) if key else ""
        if note:
            parts += [f"*{note}*", ""]

    parts += ["### What this does not measure", "", CAVEAT, ""]

    path = out_dir / "report.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


# -----------------------------------------------
# PDF writer
# -----------------------------------------------

def write_pdf(df, lexical, tables, folder, out_dir, chart_path) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    path = out_dir / "report.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="Readability report", author="readability-stats",
    )
    content_width = doc.width

    # Must happen before any style names the font: the direction arrows are
    # outside WinAnsi and Helvetica would drop them without saying so.
    base_font = register_unicode_font()
    bold_font = f"{base_font}-Bold" if base_font != "Helvetica" else "Helvetica-Bold"

    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=base_font,
                          fontSize=9.5, leading=13, alignment=TA_JUSTIFY, spaceAfter=6)
    blurb_style = ParagraphStyle("blurb", parent=body, textColor=colors.HexColor("#555555"),
                                 alignment=0, spaceAfter=8)
    legend_style = ParagraphStyle("legend", parent=blurb_style, fontSize=8,
                                  textColor=colors.HexColor("#666666"), spaceBefore=3)
    cell = ParagraphStyle("cell", parent=styles["BodyText"], fontName=base_font,
                          fontSize=8, leading=10, spaceAfter=0)
    head_cell = ParagraphStyle("headcell", parent=cell, textColor=colors.white,
                               fontName=bold_font)
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=20, spaceAfter=14)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=14,
                        spaceAfter=6, textColor=colors.HexColor("#1a1a1a"))

    story = [Paragraph("Readability report", h1)]

    # --- summary ---
    summary_rows = [[Paragraph(f"<b>{k}</b>", cell), Paragraph(str(v), cell)]
                    for k, v in summary_lines(df, folder)]
    summary_table = Table(summary_rows, colWidths=[4.2 * cm, content_width - 4.2 * cm])
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [summary_table, Spacer(1, 10)]

    if not lexical:
        story.append(Paragraph(
            "<i>NLTK's punkt/stopwords data could not be downloaded, so the TTR and MTLD "
            "columns are omitted. Everything else is unaffected.</i>", body))

    def build_table(headers, rows):
        # The chapter column wraps as a Paragraph so long filenames don't overflow;
        # numeric columns stay plain strings and are right-aligned.
        first_col = 5.5 * cm if len(headers) <= 6 else 4.5 * cm
        others = (content_width - first_col) / max(len(headers) - 1, 1)
        data = [[Paragraph(headers[0], head_cell)] + [Paragraph(h, head_cell) for h in headers[1:]]]
        for r in rows:
            data.append([Paragraph(str(r[0]), cell)] + list(r[1:]))

        t = Table(data, colWidths=[first_col] + [others] * (len(headers) - 1), repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
            ("FONTNAME", (0, 0), (-1, -1), base_font),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (1, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cfd8dc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    for key, title, blurb in SECTIONS:
        headers, rows = tables[key]
        block = [
            Paragraph(title, h2),
            Paragraph(blurb, blurb_style),
            build_table(headers, rows),
        ]
        note = table_legend(key, lexical)
        if note:
            block.append(Paragraph(note.replace("\n", "<br/>"), legend_style))
        story.append(KeepTogether(block))

    # --- chart ---
    if chart_path.exists():
        img_w, img_h = ImageReader(str(chart_path)).getSize()
        scaled_h = content_width * img_h / img_w
        story += [
            Paragraph("Pacing curve", h2),
            Paragraph("Flesch score across chapter order. The shaded bands are Flesch's own; "
                      "the dashed outline is the 60-80 target zone for fiction.", blurb_style),
            Image(str(chart_path), width=content_width, height=scaled_h),
        ]

    # --- glossary ---
    story.append(PageBreak())
    story.append(Paragraph("What each statistic means", h2))
    for key, term, explanation in GLOSSARY:
        story.append(Paragraph(f"<b>{term}</b> — {explanation}", body))
        note = range_note(key) if key else ""
        if note:
            story.append(Paragraph(note, legend_style))

    story.append(Paragraph("What this does not measure", h2))
    story.append(Paragraph(CAVEAT, body))

    doc.build(story)
    return path


# -----------------------------------------------
# Snapshots — every run kept, so drafts can be compared
# -----------------------------------------------

def new_snapshot_dir(root: Path) -> Path:
    """reports/2026-08-30-1912/, suffixed if that minute is already taken."""
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    candidate = root / stamp
    n = 2
    while candidate.exists():
        candidate = root / f"{stamp}-{n}"
        n += 1
    return candidate


def write_summary(df: pd.DataFrame, folder: str, snap_dir: Path) -> None:
    """One small machine-readable file per snapshot; the index is rebuilt from these."""
    (snap_dir / "summary.json").write_text(json.dumps({
        "snapshot":    snap_dir.name,
        "generated":   datetime.now().isoformat(timespec="seconds"),
        "source":      folder,
        "chapters":    len(df),
        "words":       int(df["words"].sum()),
        "mean_flesch": round(float(df["flesch"].mean()), 2),
        "mean_fog":    round(float(df["fog"].mean()), 2),
    }, indent=2), encoding="utf-8")


def update_latest(root: Path, snap_dir: Path) -> None:
    """reports/latest → the newest snapshot, so one path always works."""
    latest = root / "latest"
    try:
        if latest.is_symlink():
            latest.unlink()
        elif latest.exists():
            return   # a real directory sits there; leave it alone
        latest.symlink_to(snap_dir.name)
    except OSError:
        pass         # symlinks unavailable (e.g. some network volumes) — not fatal


def write_index(root: Path) -> Path | None:
    """
    Rebuild reports/index.md from every snapshot's summary.json, so the trend across
    drafts is visible at a glance and deleted snapshots simply drop out.
    """
    snaps = []
    for f in sorted(root.glob("*/summary.json")):
        if f.parent.is_symlink():
            continue   # 'latest' points at a real snapshot; don't count it twice
        try:
            snaps.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    if not snaps:
        return None

    snaps.sort(key=lambda s: s.get("generated", ""))

    lines = ["# Report snapshots", "",
             f"{len(snaps)} snapshot{'s' if len(snaps) != 1 else ''}, oldest first. "
             "Change columns compare each run with the one before it.", "",
             md_table(
                 ["Snapshot", "Chapters", "Words", "Words change", "Mean Flesch",
                  "Flesch change", "Report"],
                 [[s["snapshot"],
                   f"{s['chapters']:,}",
                   f"{s['words']:,}",
                   "—" if i == 0 else f"{s['words'] - snaps[i - 1]['words']:+,}",
                   f"{s['mean_flesch']:.1f}",
                   "—" if i == 0 else f"{s['mean_flesch'] - snaps[i - 1]['mean_flesch']:+.1f}",
                   f"[md]({s['snapshot']}/report.md) · [pdf]({s['snapshot']}/report.pdf)"]
                  for i, s in enumerate(snaps)]),
             ""]

    path = root / "index.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# -----------------------------------------------

def main(folder: str = MANUSCRIPT, output_dir: str | None = None) -> None:
    snapshot = output_dir is None
    root = Path(REPORTS_DIR)
    out_dir = new_snapshot_dir(root) if snapshot else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df, lexical = build_dataframe(folder)
    if df.empty:
        print(f"No .md or .docx files with readable text found in: {folder}")
        if snapshot:
            out_dir.rmdir()   # don't leave an empty snapshot behind
        return

    tables = table_data(df, lexical)
    chart_path = plot_pacing_curve(df, str(out_dir / "pacing_curve.png"))

    md_path  = write_markdown(df, lexical, tables, folder, out_dir, chart_path.name)
    pdf_path = write_pdf(df, lexical, tables, folder, out_dir, chart_path)

    print(f"{len(df)} chapters, {int(df['words'].sum()):,} words")
    if not lexical:
        print("Note: NLTK data unavailable — TTR and MTLD omitted.")
    for p in (md_path, pdf_path, chart_path):
        print(f"Saved: {p.resolve()}")

    if snapshot:
        write_summary(df, folder, out_dir)
        update_latest(root, out_dir)
        index = write_index(root)
        if index:
            print(f"Index: {index.resolve()}")


if __name__ == "__main__":
    folder     = sys.argv[1] if len(sys.argv) > 1 else MANUSCRIPT
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    main(folder, output_dir)
