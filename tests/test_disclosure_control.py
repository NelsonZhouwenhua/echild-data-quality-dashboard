import pandas as pd

from src.disclosure_control import suppress_count, suppress_small_counts


def test_small_nonzero_count_is_suppressed():
    assert suppress_count(4, threshold=10) == "<10"
    assert suppress_count(0, threshold=10) == 0
    assert suppress_count(12, threshold=10) == 12


def test_table_suppression_changes_only_requested_columns():
    frame = pd.DataFrame({"group": ["a", "b"], "count": [4, 12], "rate": [0.2, 0.4]})
    display = suppress_small_counts(frame, ["count"], threshold=10)
    assert list(display["count"]) == ["<10", 12]
    assert list(display["rate"]) == [0.2, 0.4]
