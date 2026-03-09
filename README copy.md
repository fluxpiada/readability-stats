# readability-stats

Python scripts that analyse the readability and pacing of a markdown-based manuscript.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

All scripts accept an optional folder argument. The default points to the manuscript path hardcoded in each file — edit `MANUSCRIPT` in any script, or pass the path at runtime:

```bash
python 01_readability.py /path/to/your/manuscript
```

## Scripts

| Script | What it does |
|---|---|
| `01_readability.py` | Flesch, FK Grade, Gunning Fog per chapter; sorted summary table |
| `02_convert_md_txt.py` | Strips markdown and writes plain `.txt` files to `converted_txt/` |
| `03_readability_vs_story_order.py` | Plots Flesch score across chapter order → `pacing_curve.png` |
| `04_sentence_length_histo.py` | Sentence-length histogram per chapter → `sentence_histograms/` |
| `05_lexical_div.py` | TTR and MTLD lexical diversity per chapter |
| `06_complex_deltas.py` | Chapter-to-chapter deltas in Flesch, Fog, and word count |
| `07_tightening.py` | Ranks chapters by tightening priority (wordiness + density score) |
| `countwords.py` | Word count per chapter and total |

## Shared code

`utils.py` contains all shared functions: `strip_markdown`, `count_syllables`, `readability_metrics`, and `load_chapters`. Edit here, not in individual scripts.
