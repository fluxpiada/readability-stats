"""
01_readability.py — print readability metrics for every chapter, sorted by difficulty.
Usage: python 01_readability.py [folder]
"""

from read_stats import band, header, legend, load_chapters, readability_metrics, resolve_folder


def main(folder: str) -> None:
    stats = []
    for filename, text in load_chapters(folder):
        m = readability_metrics(text)
        if m:
            stats.append((filename, m))

    if not stats:
        print("No .md files found.")
        return

    print(f"Readability results for: {folder}\n")
    for filename, m in stats:
        print(f"--- {filename} ---")
        print(f"  Words:        {m['words']}")
        print(f"  Sentences:    {m['sentences']}")
        print(f"  Flesch:       {m['flesch']:.2f}  ({band(m['flesch'])})")
        print(f"  FK Grade:     {m['fk_grade']:.2f}")
        print(f"  Gunning Fog:  {m['gunning_fog']:.2f}")
        print()

    print("\n=== Summary (hardest → easiest by Flesch) ===\n")
    stats_sorted = sorted(stats, key=lambda x: x[1]["flesch"])
    flesch_h, fk_h, fog_h = header("flesch"), header("fk"), header("fog")
    print(f"{flesch_h:>9}  {fk_h:>6}  {fog_h:>6}  {'Words':>6}  File")
    print("-" * 70)
    for filename, m in stats_sorted:
        print(f"{m['flesch']:9.2f}  {m['fk_grade']:6.2f}  {m['gunning_fog']:6.2f}  "
              f"{m['words']:6d}  {filename}")

    print()
    print(legend(["flesch", "fk", "fog"]))


if __name__ == "__main__":
    folder = resolve_folder()
    main(folder)
