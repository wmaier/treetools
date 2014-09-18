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
    assert len(cont_grammar.keys()) \
        == len(testdata.CONT_GRAMMAR_FUNCS)
    assert all([func in testdata.CONT_GRAMMAR_FUNCS \
                    for func in cont_grammar.keys()])
    lins = [lin for lin in cont_grammar[func] for func in cont_grammar]
    assert len(lins) == 6
    assert all([lin == (((0, 0),),) for lin in lins])


def test_discont_grammar(discont_grammar):
    """Test grammar extraction from discontinuous trees
    """
    assert len(discont_grammar.keys()) \
        == len(testdata.DISCONT_GRAMMAR_FUNCS)
    assert all([func in testdata.DISCONT_GRAMMAR_FUNCS \
                    for func in discont_grammar.keys()])
    lins = [lin for lin in discont_grammar[func] for func in discont_grammar]
    assert len(lins) == len(testdata.DISCONT_GRAMMAR_LINS)
    assert all([lin in testdata.DISCONT_GRAMMAR_LINS for lin in lins])


def test_binarize_leftright(discont_grammar, cont_grammar):
    """Test left-to-right binarization
    """
    discont_grammar = grammar.binarize(discont_grammar)
    cont_grammar = grammar.binarize(cont_grammar)
    assert testdata.DISCONT_GRAMMAR_LEFT_RIGHT == discont_grammar
    assert testdata.CONT_GRAMMAR_LEFT_RIGHT == cont_grammar

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
