"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
from trees import grammar
from . import testdata


def test_cont_grammar(cont_grammar):
    """Test grammar extraction from non-discontinuous trees
    """
    funcs = cont_grammar.keys()
    assert len(set(testdata.CONT_GRAMMAR_FUNCS) - set(funcs)) == 0


@pytest.fixture(scope='function')
def cont_grammar(cont_tree):
    gram = {}
    lex = {}
    grammar.extract(cont_tree, gram, lex)
    return gram


@pytest.fixture(scope='function')
def discont_grammar(discont_tree):
    gram = {}
    lex = {}
    grammar.extract(discont_tree, gram, lex)
    return gram
