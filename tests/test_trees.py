"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
from StringIO import StringIO
from trees import trees, treeinput, treeoutput, transform, treeanalysis
from . import constants

def test_labels():
    """General test concerning the parsing and output of labels
    """
    label = ""
    e = trees.parse_label(label)
    assert e.label == trees.DEFAULT_LABEL
    assert e.gf == trees.DEFAULT_EDGE
    assert e.gf_separator == trees.DEFAULT_GF_SEPARATOR
    assert e.coindex == ""
    assert e.gapindex == ""
    assert not e.headmarker
    assert not e.is_trace
    olabel = trees.format_label(e)
    assert olabel == label
    label = "-NONE-"
    e = trees.parse_label(label)
    assert e.label == "-NONE-"
    assert not e.is_trace
    olabel = trees.format_label(e)
    assert olabel == label
    label = "A--A=1---2"
    e = trees.parse_label(label)
    assert e.label == "A--A=1--"
    assert e.gf == trees.DEFAULT_EDGE
    assert e.coindex == "2"
    assert not e.is_trace
    olabel = trees.format_label(e)
    assert olabel == label
    label = "A--A-1--=2"
    e = trees.parse_label(label)
    assert e.label == "A--A-1--"
    assert e.gf == trees.DEFAULT_EDGE
    assert e.coindex == ""
    assert e.gapindex == "2"
    assert not e.is_trace
    olabel = trees.format_label(e)
    assert olabel == label
    label = "*LAB*-GF=1'"
    e = trees.parse_label(label)
    assert e.label == "*LAB*"
    assert e.gf == "GF"
    assert e.gapindex == "1"
    assert e.headmarker 
    assert e.is_trace
    olabel = trees.format_label(e)
    assert olabel == label


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
    assert all(['num' in node.data for node in terms])
    assert all([node in uterms for node in terms])
    assert len(terms) == 9
    assert len(uterms) == 9
    assert len(nodes) == 15
    assert labels == testdata.CONT_LABELS_PREORDER
    assert words == testdata.WORDS
    assert set(uwords) == set(testdata.WORDS)


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
    assert all(['num' in node.data for node in terms])
    assert all([node in uterms for node in terms])
    assert len(terms) == 9
    assert len(uterms) == 9
    assert len(nodes) == 15
    assert labels == testdata.DISCONT_LABELS_PREORDER
    assert words == testdata.WORDS
    assert set(uwords) == set(testdata.WORDS)


def test_discont_output(discont_tree):
    """Test tree output
    """
    stream = StringIO()
    # export: check if all fields are the same
    treeoutput.export(discont_tree, stream)
    result = stream.getvalue()
    original = testdata.SAMPLE_EXPORT
    for result_line, original_line in zip(result.split('\n'), original.split('\n')):
        for result_f, original_f in zip(result_line.split(), original_line.split()):
            assert result_f == original_f
    treeoutput.compute_export_numbering(discont_tree)
    numbers = [node.data['num'] for node in trees.preorder(discont_tree)]
    assert numbers == testdata.DISCONT_EXPORT_NUMBERING
    # tigerxml: check linewise if output is the same as sample
    stream = StringIO()
    treeoutput.tigerxml(discont_tree, stream)
    result = stream.getvalue()
    original = '\n'.join(testdata.SAMPLE_TIGERXML.split('\n')[3:-3])
    for result_line, original_line in zip(result.split('\n'), original.split('\n')):
        assert result_line == original_line


def test_cont_output(cont_tree):
    """Test continuous tree output
    """
    tree = cont_tree
    # brackets
    stream = StringIO()
    original = testdata.SAMPLE_BRACKETS.replace('\n', '')
    treeoutput.brackets(cont_tree, stream, brackets_emptyroot=True)
    result = stream.getvalue().strip()
    assert result == original
    stream = StringIO()
    original = original[:1] + trees.DEFAULT_ROOT + original[1:]
    treeoutput.brackets(cont_tree, stream)
    result = stream.getvalue().strip()
    assert result == original


def test_lca(discont_tree, cont_tree):
    """trees.lca
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
    """trees.right_sibling
    """
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
    assert rs == testdata.DISCONT_RIGHTSIB_PREORDER
    assert crs == testdata.CONT_RIGHTSIB_PREORDER


def test_terminal_blocks(discont_tree, cont_tree):
    """trees.terminal_blocks
    """
    for node in trees.preorder(discont_tree):
        if node.data['label'] == 'VP':
            blocks = [set([term.data['num'] for term in block]) for block 
                      in trees.terminal_blocks(node)]
            assert blocks == [set(block) for block in testdata.DISCONT_BLOCKS_VP]
            break
    for node in trees.preorder(cont_tree):
        if node.data['label'] == 'VP':
            blocks = [set([term.data['num'] for term in block]) for block 
                      in trees.terminal_blocks(node)]
            assert blocks == [set(block) for block in testdata.CONT_BLOCKS_VP]
            break


def test_dominance(discont_tree, cont_tree):
    """trees.dominance
    """
    dterms = trees.terminals(discont_tree)
    ddom = [node.data['label'] for node in trees.dominance(dterms[0])]
    cterms = trees.terminals(cont_tree)
    cdom = [node.data['label'] for node in trees.dominance(cterms[0])]
    assert ddom == testdata.DISCONT_DOM_FIRST
    assert cdom == testdata.CONT_DOM_FIRST


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
    assert labels == testdata.DISCONT_LABELS_PREORDER
    assert words == testdata.WORDS
    assert set(uwords) == set(testdata.WORDS)
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
    assert labels == testdata.DISCONT_LABELSBOYD_PREORDER
    assert words == testdata.WORDS
    assert set(uwords) == set(testdata.WORDS)


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
    assert labels == testdata.CONT_LABELS_PREORDER
    assert words == testdata.WORDS
    assert set(uwords) == set(testdata.WORDS)


def test_analysis(discont_tree, cont_tree):
    """See treeanalysis
    """
    gapdegree = treeanalysis.GapDegree()
    gapdegree.run(cont_tree)
    gapdegree.run(discont_tree)
    assert sum(gapdegree.gaps_per_tree.values()) == 2
    assert sum(gapdegree.gaps_per_node.values()) == 12
    assert gapdegree.gaps_per_tree[0] == 1
    assert gapdegree.gaps_per_tree[1] == 1
    assert gapdegree.gaps_per_node[0] == 9
    assert gapdegree.gaps_per_node[1] == 3
    assert treeanalysis.gap_degree(discont_tree) == 1
    assert treeanalysis.gap_degree(cont_tree) == 0
    treeoutput.compute_export_numbering(discont_tree)
    for node in trees.preorder(discont_tree):
        if node.data['num'] in [500, 502, 503]:
            assert treeanalysis.gap_degree_node(node) == 1
        else:
            assert treeanalysis.gap_degree_node(node) == 0
    postags = treeanalysis.PosTags()
    postags.run(discont_tree)
    assert postags.tags == testdata.POS 
    sentencecount = treeanalysis.SentenceCount()
    sentencecount.run(discont_tree)
    sentencecount.run(cont_tree)
    assert sentencecount.cnt == 2
