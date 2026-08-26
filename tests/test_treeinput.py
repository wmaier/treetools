"""Tests for tree input formats."""

from treetools import treeinput, trees
from . import testdata


def test_discobrackets_reordered_uses_original_token_indices(tmp_path):
    source = tmp_path / "trees.discobrackets"
    source.write_text(
        testdata.SAMPLE_DISCOBRACKETS_OUTPUT_DISCONT + "\n",
        encoding="utf-8")

    tree = next(treeinput.discobrackets(
        str(source), "utf-8", quiet=True, disco_reordered=True))
    terminals = [(terminal.data['num'], terminal.data['word'])
                 for terminal in trees.terminals(tree)]

    assert terminals == [
        (1, '1-Who'),
        (2, '8-likes'),
        (3, '6-that'),
        (4, '7-Manfred'),
        (5, '4-tell'),
        (6, '5-Hans'),
        (7, '2-did'),
        (8, '3-Fritz'),
        (9, '9-?'),
    ]
