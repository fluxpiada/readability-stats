"""
03_readability_vs_story_order.py — plot Flesch score across chapter order (pacing curve).
Usage: python 03_readability_vs_story_order.py [folder]
"""

from read_stats import chapter_frame, plot_pacing_curve, resolve_folder

if __name__ == "__main__":
    folder = resolve_folder()
    df, _ = chapter_frame(folder)
    written = plot_pacing_curve(df)
    print(f"Saved: {written.resolve()}")
