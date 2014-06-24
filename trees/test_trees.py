"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest)

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
import tempfile
import os
import sys
from copy import deepcopy
from StringIO import StringIO
from . import trees, treeinput, transform

BRACKETS_SAMPLE = """
((S(WP Who)(VB did)(NNP Fritz)(VP(VB tell)(NNP Hans)(SBAR(IN that)
(NP(NNP Manfred))(VP(VB likes)))))(? ?))
"""
EXPORT_SAMPLE = """
#BOS 1
Who			WP	--		--	501
did			VB	--       	HD	504
Fritz     		NNP	--		HD	504
tell			VB	--		HD	503
Hans			NNP	--		--	503
that			IN	--       	HD	502
Manfred  		NNP	--		HD	500
likes			VB	--		HD	501
?			?	--		--	0
#500			NP	--		--	502
#501			VP	--		--	502
#502			SBAR	--		--	503
#503			VP	--		--	504
#504			S	--		--	0
#EOS 1
"""
TIGERXML_SAMPLE = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<corpus>
<body>
<s id="1">
<graph root="0">
  <terminals>
    <t id="1" word="Who" lemma="--" pos="WP" morph="--" />
    <t id="2" word="did" lemma="--" pos="VB" morph="--" />
    <t id="3" word="Fritz" lemma="--" pos="NNP" morph="--" />
    <t id="4" word="tell" lemma="--" pos="VB" morph="--" />
    <t id="5" word="Hans" lemma="--" pos="NNP" morph="--" />
    <t id="6" word="that" lemma="--" pos="IN" morph="--" />
    <t id="7" word="Manfred" lemma="--" pos="NNP" morph="--" />
    <t id="8" word="likes" lemma="--" pos="VB" morph="--" />
    <t id="9" word="?" lemma="--" pos="?" morph="--" />
  </terminals>
  <nonterminals>
    <nt id="500" cat="VP">
      <edge label="--" idref="1" />
      <edge label="HD" idref="8" />
    </nt>
    <nt id="501" cat="NP">
      <edge label="HD" idref="7" />
    </nt>
    <nt id="502" cat="SBAR">
      <edge label="--" idref="500" />
      <edge label="HD" idref="6" />
      <edge label="--" idref="501" />
    </nt>
    <nt id="503" cat="VP">
      <edge label="--" idref="502" />
      <edge label="HD" idref="4" />
      <edge label="--" idref="5" />
    </nt>
    <nt id="504" cat="S">
      <edge label="--" idref="503" />
      <edge label="HD" idref="2" />
      <edge label="HD" idref="3" />
    </nt>
    <nt id="0" cat="VROOT">
      <edge label="--" idref="504" />
      <edge label="--" idref="9" />
    </nt>
  </nonterminals>
</graph>
</s>
</body>
</corpus>
"""
WORDS = [u'Who', u'did', u'Fritz', u'tell', u'Hans',
         u'that', u'Manfred', u'likes', u'?']
PREORDER_LABELS_DISCONT = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                   u'VB', u'IN', u'NP', u'NNP', u'VB', u'NNP',
                   u'VB', u'NNP', u'?']
PREORDER_RIGHT_SIBLINGS_DISCONT = [None, u'?', u'VB', u'VB', u'IN', u'VB', 
                           None, u'NP', None, None, u'NNP', None, 
                           u'NNP', None, None]
PREORDER_LABELS_BOYD = [u'VROOT', u'S', u'VP', u'SBAR', u'VP',
                        u'WP', u'VB', u'NNP', u'VP', u'VB',
                        u'NNP', u'SBAR', u'IN', u'NP', u'NNP',
                        u'VP', u'VB', u'?']
PREORDER_LABELS_CONT = [u'VROOT', u'S', u'WP', u'VB', u'NNP',
                           u'VP', u'VB', u'NNP', u'SBAR', u'IN',
                           u'NP', u'NNP', u'VP', u'VB', u'?']
PREORDER_RIGHT_SIBLINGS_CONT = [None, u'?', u'VB', u'NNP', u'VP', 
                                None, u'NNP', u'SBAR', None, u'NP', 
                                u'VP', None, None, None, None]


def test_cont_general(cont_tree):
    """General tests concerning continuous trees.
    """
    tree = cont_tree
    terms = trees.terminals(tree)
    uterms = trees.unordered_terminals(tree)
    nodes = [node for node in trees.preorder(tree)]
    labels = [node.data['label'] for node in nodes]
    words = [node.data['word'] for node in terms]
    uwords = [node.data['word'] for node in uterms]
    assert len(terms) == 9
    assert len(uterms) == 9
    assert len(nodes) == 15
    assert labels == PREORDER_LABELS_CONT
    assert words == WORDS
    assert set(uwords) == set(WORDS)


def test_discont_general(discont_tree):
    """General tests concerning discontinuous trees.
    """
    tree = discont_tree
    nodes = [node for node in trees.preorder(tree)]
    labels = [node.data['label'] for node in nodes]
    terms = trees.terminals(tree)
    words = [node.data['word'] for node in terms]
    uterms = trees.unordered_terminals(tree)
    uwords = [node.data['word'] for node in uterms]
    assert len(terms) == 9
    assert len(uterms) == 9
    assert len(nodes) == 15
    assert labels == PREORDER_LABELS_DISCONT
    assert words == WORDS
    assert set(uwords) == set(WORDS)


def test_lca(discont_tree, cont_tree):
    """Least common ancestor.
    """
    tree = discont_tree
    ctree = cont_tree
    terms = trees.terminals(tree)
    cterms = trees.terminals(ctree)
    root_children = trees.children(tree)
    croot_children = trees.children(ctree)
    lca = trees.lca(terms[0], terms[1])
    clca = trees.lca(cterms[0], cterms[1])
    assert terms[0].data['word'] == 'Who'
    assert cterms[0].data['word'] == 'Who'
    assert terms[1].data['word'] == 'did'
    assert cterms[1].data['word'] == 'did'
    assert root_children[0].data['label'] == 'S'
    assert croot_children[0].data['label'] == 'S'
    assert root_children[0] == lca
    assert croot_children[0] == clca


def test_right_sibling(discont_tree, cont_tree):
    tree = discont_tree
    rs = []
    for node in trees.preorder(discont_tree):
        sibling = trees.right_sibling(node)
        if sibling is None:
            rs.append(sibling)
        else:
            rs.append(sibling.data['label'])
    ctree = cont_tree
    crs = []
    for node in trees.preorder(cont_tree):
        sibling = trees.right_sibling(node)
        if sibling is None:
            crs.append(sibling)
        else:
            crs.append(sibling.data['label'])
    assert rs == PREORDER_RIGHT_SIBLINGS_DISCONT
    assert crs == PREORDER_RIGHT_SIBLINGS_CONT


def test_root_attach(discont_tree):
    """See transform.root_attach
    """
    tree = discont_tree
    tree = transform.root_attach(tree)
    nodes = [node for node in trees.preorder(tree)]
    labels = [node.data['label'] for node in nodes]
    terms = trees.terminals(tree)
    words = [node.data['word'] for node in terms]
    uterms = trees.unordered_terminals(tree)
    uwords = [node.data['word'] for node in uterms]
    assert labels == PREORDER_LABELS_DISCONT
    assert words == WORDS
    assert set(uwords) == set(WORDS)
    with pytest.raises(ValueError):
        transform.boyd_split(tree)


def test_boyd(discont_tree):
    """See transform.boyd_split
    """
    tree = discont_tree
    tree = transform.root_attach(tree)
    tree = transform.negra_mark_heads(tree)
    tree = transform.boyd_split(tree)
    nodes = [node for node in trees.preorder(tree)]
    labels = [node.data['label'] for node in nodes]
    terms = trees.terminals(tree)
    words = [node.data['word'] for node in terms]
    uterms = trees.unordered_terminals(tree)
    uwords = [node.data['word'] for node in uterms]
    assert labels == PREORDER_LABELS_BOYD
    assert words == WORDS
    assert set(uwords) == set(WORDS)


def test_raising(discont_tree):
    """See transform.raising
    """
    tree = discont_tree
    tree = transform.root_attach(tree)
    tree = transform.negra_mark_heads(tree)
    tree = transform.boyd_split(tree)
    tree = transform.raising(tree)
    nodes = [node for node in trees.preorder(tree)]
    labels = [node.data['label'] for node in nodes]
    terms = trees.terminals(tree)
    words = [node.data['word'] for node in terms]
    uterms = trees.unordered_terminals(tree)
    uwords = [node.data['word'] for node in uterms]
    assert labels == PREORDER_LABELS_CONT
    assert words == WORDS
    assert set(uwords) == set(WORDS)


@pytest.fixture(scope='function',
                params=[(treeinput.tigerxml, TIGERXML_SAMPLE),
                        (treeinput.export, EXPORT_SAMPLE)])
def discont_tree(request):
    """Load discontinuous tree samples
    """
    tempfile_name = None
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        tempfile_name = temp.name
        temp.write(request.param[1])
        temp.flush()
    params = {'quiet' : True}
    reader = request.param[0](tempfile_name, 'utf8', **params)
    def fin():
        os.remove(tempfile_name)
    request.addfinalizer(fin)
    return reader.next()


@pytest.fixture(scope='function',
                params=[(treeinput.brackets, BRACKETS_SAMPLE)])
def cont_tree(request):
    """Load continuous tree samples
    """
    tempfile_name = None
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        tempfile_name = temp.name
        temp.write(request.param[1])
        temp.flush()
    params = {'quiet' : True}
    reader = request.param[0](tempfile_name, 'utf8', **params)
    def fin():
        os.remove(tempfile_name)
    return reader.next()

