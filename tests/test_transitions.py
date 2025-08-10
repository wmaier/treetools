"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
from treetools import transitions, transform
from . import testdata_transitions


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
