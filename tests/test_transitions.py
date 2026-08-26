"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
from types import SimpleNamespace
from treetools import transitions, transform
from . import testdata, testdata_transitions


def test_topdown_cont_negra(cont_tree):
    tree = transform.negra_mark_heads(cont_tree)
    tree = transform.binarize(tree)
    terms, trans = transitions.topdown(cont_tree)
    assert testdata_transitions.TRANS_CONT_TOPDOWN_NEGRAHEADS_TRANSITIONS == [
        str(t) for t in trans]
    assert testdata_transitions.TRANS_TERMINALS == terms

def test_gap_discont_negra(discont_tree):
    tree = transform.negra_mark_heads(discont_tree)
    tree = transform.binarize(tree)
    terms, trans = transitions.gap(tree)
    assert testdata_transitions.TRANS_DISCONT_GAP_TRANSITIONS == [str(t) for t in trans]
    assert testdata_transitions.TRANS_TERMINALS == terms


def test_run_skips_trees_filtered_by_transform(tmp_path):
    source = tmp_path / "trees.brackets"
    destination = tmp_path / "transitions.txt"
    source.write_text(testdata.SAMPLE_BRACKETS, encoding="utf-8")
    args = SimpleNamespace(
        src=str(source), dest=str(destination), transtype='topdown',
        transform=['filter_by_length'],
        transformparams=['filteroperator:gt', 'filtervalue:0'],
        src_format='brackets', src_enc='utf-8', src_opts=[],
        dest_format='plain', dest_enc='utf-8', dest_opts=[])

    with pytest.raises(SystemExit):
        transitions.run(args)

    assert destination.read_text(encoding="utf-8") == ""
