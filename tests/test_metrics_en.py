"""
Range, direction and target metadata for the English statistics.

Same guard as the Dutch side: catch a column that gets added without telling
the reader how to read it, and stop a statistic with no better end from
acquiring an invented target.
"""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import read_stats  # noqa: E402

report = importlib.import_module("08_report")


@pytest.mark.parametrize("key, metric", sorted(read_stats.METRICS.items()))
def test_metric_is_fully_populated(key, metric):
    assert metric.label.strip()
    assert metric.span.strip()
    assert metric.better in read_stats.DIRECTIONS
    assert metric.target.strip()
    assert metric.source.strip()


@pytest.mark.parametrize("key, metric", sorted(read_stats.METRICS.items()))
def test_no_direction_means_no_target(key, metric):
    """
    A statistic with no better end must not carry a target zone. Deltas are the
    case that matters: a big change of gear between chapters can be exactly
    right, so "aim for a small delta" would be wrong advice.
    """
    if metric.better == "none":
        assert not metric.has_target, f"{key} has no direction but does have a target"


def test_every_table_column_has_a_metric():
    """Catches: someone adds a column and forgets the metadata."""
    for section in report.SECTIONS:
        for column in section.columns:
            if column.metric is None:
                continue
            assert column.metric in read_stats.METRICS, (
                f"column '{column.field}' in table '{section.key}' has no metric entry"
            )


def test_every_table_has_a_legend():
    for section in report.SECTIONS:
        assert report.table_legend(section.key).strip()


def test_legend_explains_every_symbol_it_shows():
    for section in report.SECTIONS:
        text = report.table_legend(section.key)
        for column in section.columns:
            if column.metric is None:
                continue
            symbol = read_stats.METRICS[column.metric].symbol
            assert symbol in text, (
                f"symbol {symbol} for '{column.field}' missing from "
                f"the '{section.key}' legend"
            )


def test_every_column_names_a_real_dataframe_field():
    """Catches: a column spec that points at a field chapter_frame never builds."""
    import inspect

    source = inspect.getsource(read_stats.chapter_frame)
    for section in report.SECTIONS:
        for column in section.columns:
            assert f'"{column.field}"' in source, (
                f"column '{column.field}' in table '{section.key}' "
                "is not a column chapter_frame produces"
            )


def test_legend_drops_lexical_columns_when_nltk_is_missing():
    """
    Without NLTK the TTR and MTLD columns are omitted from the table, so the
    legend must not still promise an MTLD target.
    """
    text = report.table_legend("per_chapter", lexical=False)
    assert "MTLD" not in text
    assert "Flesch" in text


def test_glossary_keys_resolve():
    for key, term, explanation in report.GLOSSARY:
        assert term.strip() and explanation.strip()
        if key is not None:
            assert key in read_stats.METRICS, f"glossary entry '{term}' has an unknown key"


def test_header_appends_the_symbol():
    assert read_stats.header("flesch") == "Flesch ↑"
    assert read_stats.header("fog") == "Fog ↓"
    assert read_stats.header("delta", "Flesch change") == "Flesch change •"


def test_header_of_an_unknown_column_is_unchanged():
    assert read_stats.header("chapter", "Chapter") == "Chapter"


def test_range_note_records_where_the_target_came_from():
    """Our editorial guesses must not read like published bands."""
    assert "ours" in read_stats.range_note("mtld")
    assert "Flesch's own" in read_stats.range_note("flesch")


def test_range_note_promises_nothing_without_a_target():
    note = read_stats.range_note("delta")
    assert "no target" in note.lower()
    assert "Aim" not in note
