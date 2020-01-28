"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
import io
import os
from trees import transitions, transitionoutput, transform
from . import testdata_transitions, testdata


def test_topdown_cont_negra(cont_tree):
    tree = transform.negra_mark_heads(cont_tree)
    tree = transform.binarize(tree)
    terms, trans = transitions.topdown(cont_tree)
    assert testdata_transitions.TRANS_CONT_TOPDOWN_NEGRAHEADS_TRANSITIONS == [
        str(t) for t in trans]
    assert testdata_transitions.TRANS_CONT_TOPDOWN_NEGRAHEADS_TERMINALS == terms
