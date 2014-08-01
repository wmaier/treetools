"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
import tempfile
import sys
from StringIO import StringIO
from trees import trees, treeinput, treeoutput, transform, treeanalysis
from . import testdata


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


def test_delete_terminal(discont_tree, cont_tree):
    """trees.delete_terminal
    """
    # discont
    old_num_nodes = len([node for node in trees.preorder(discont_tree)])
    terminals = trees.terminals(discont_tree)
    to_remove = terminals[0]
    to_remove_p = to_remove.parent
    result = trees.delete_terminal(discont_tree, to_remove)
    res_words = [node.data['word'] for node in trees.terminals(discont_tree)]
    res_num_nodes = len([node for node in trees.preorder(discont_tree)])
    assert result == to_remove_p
    assert res_words == testdata.WORDS[1:]
    assert res_num_nodes == old_num_nodes - 1
    # cont
    old_num_nodes = len([node for node in trees.preorder(cont_tree)])
    terminals = trees.terminals(cont_tree)
    to_remove = terminals[0]
    to_remove_p = to_remove.parent
    result = trees.delete_terminal(cont_tree, to_remove)
    res_words = [node.data['word'] for node in trees.terminals(cont_tree)]
    res_num_nodes = len([node for node in trees.preorder(cont_tree)])
    assert result == to_remove_p
    assert res_words == testdata.WORDS[1:]
    assert res_num_nodes == old_num_nodes - 1


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


def test_add_topnode(discont_tree, cont_tree):
    """transform.add_topnode
    """
    dtree = discont_tree
    discont_nodes = [node for node in trees.preorder(dtree)]
    dtree = transform.add_topnode(dtree)
    discont_nodes_p = [node for node in trees.preorder(dtree)]
    assert len(discont_nodes) == len(discont_nodes_p) - 1
    assert discont_tree.parent == dtree
    assert len(trees.children(dtree)) == 1
    ctree = cont_tree
    cont_nodes = [node for node in trees.preorder(ctree)]
    ctree = transform.add_topnode(ctree)
    cont_nodes_p = [node for node in trees.preorder(ctree)]
    assert len(cont_nodes) == len(cont_nodes_p) - 1
    assert cont_tree.parent == ctree
    assert len(trees.children(ctree)) == 1


def test_insert_terminal(discont_tree, cont_tree):
    """transform.insert_terminals
    """
    temp = tempfile.NamedTemporaryFile()
    temp.write('1\t0\tTest1\tPosTest1\n')
    temp.write('1\t2\tTest1\tPosTest1\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t100\tTest2\tPosTest2\n')
    temp.flush()
    params = {'terminalfile' : temp.name, 'quiet' : True}
    with pytest.raises(ValueError):
        transform.insert_terminals(discont_tree,
                                   **params)
    temp = tempfile.NamedTemporaryFile()
    temp.write('1\t0\tTest1\tPosTest1\n')
    temp.write('1\t2\tTest1\tPosTest1\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t100\tTest2\tPosTest2\n')
    temp.flush()
    params = {'terminalfile' : temp.name, 'quiet' : True}
    old_terms = trees.terminals(discont_tree)
    discont_tree = transform.insert_terminals(discont_tree,
                                              **params)
    new_terms = trees.terminals(discont_tree)
    assert len(old_terms) == len(new_terms) - 2
    gold_words = list(testdata.WORDS)
    out_words = [term.data['word'] for term in new_terms]
    gold_words[1:1] = ['Test1']
    gold_words[5:5] = ['Test2']
    assert gold_words == out_words
    gold_pos = list(testdata.POS)
    out_pos = [term.data['label'] for term in new_terms]
    gold_pos[1:1] = ['PosTest1']
    gold_pos[5:5] = ['PosTest2']
    assert gold_pos == out_pos
    # cont
    temp = tempfile.NamedTemporaryFile()
    temp.write('1\t0\tTest1\tPosTest1\n')
    temp.write('1\t2\tTest1\tPosTest1\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t100\tTest2\tPosTest2\n')
    temp.flush()
    params = {'terminalfile' : temp.name, 'quiet' : True}
    with pytest.raises(ValueError):
        transform.insert_terminals(cont_tree,
                                   **params)
    temp = tempfile.NamedTemporaryFile()
    temp.write('1\t0\tTest1\tPosTest1\n')
    temp.write('1\t2\tTest1\tPosTest1\n')
    temp.write('1\t6\tTest2\tPosTest2\n')
    temp.write('1\t100\tTest2\tPosTest2\n')
    temp.flush()
    params = {'terminalfile' : temp.name, 'quiet' : True}
    old_terms = trees.terminals(cont_tree)
    cont_tree = transform.insert_terminals(cont_tree,
                                           **params)
    new_terms = trees.terminals(cont_tree)
    assert len(old_terms) == len(new_terms) - 2
    gold_words = list(testdata.WORDS)
    out_words = [term.data['word'] for term in new_terms]
    gold_words[1:1] = ['Test1']
    gold_words[5:5] = ['Test2']
    assert gold_words == out_words
    gold_pos = list(testdata.POS)
    out_pos = [term.data['label'] for term in new_terms]
    gold_pos[1:1] = ['PosTest1']
    gold_pos[5:5] = ['PosTest2']
    assert gold_pos == out_pos


def test_punctuation_verylow(discont_tree, cont_tree):
    """transform.punctuation_verylow
    """
    terminals = trees.terminals(discont_tree)
    old_vp_children = terminals[0].parent.children
    old_q_parent = terminals[-1].parent
    terminals[0].data['word'] = "("
    terminals[7].data['word'] = ")"
    discont_tree = transform.punctuation_verylow(discont_tree)
    new_vp_children = terminals[0].parent.children
    new_q_parent = terminals[-1].parent
    new_labels_test = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                       u'VB', u'?', u'IN', u'NP', u'NNP', u'VB', 
                       u'NNP', u'VB', u'NNP']
    assert old_q_parent == discont_tree
    assert old_vp_children == new_vp_children
    assert new_q_parent == terminals[-2].parent
    assert new_labels_test == [node.data['label'] for node in
                               trees.preorder(discont_tree)]
    terminals = trees.terminals(cont_tree)
    old_vp_children = terminals[0].parent.children
    old_q_parent = terminals[-1].parent
    terminals[0].data['word'] = "("
    terminals[7].data['word'] = ")"
    cont_tree = transform.punctuation_verylow(cont_tree)
    new_vp_children = terminals[0].parent.children
    new_q_parent = terminals[-1].parent
    new_labels_test = [u'VROOT', u'S', u'WP', u'VB', u'NNP',
                       u'VP', u'VB', u'NNP', u'SBAR', u'IN',
                       u'NP', u'NNP', u'VP', u'VB', u'?']
    assert old_q_parent == cont_tree
    assert old_vp_children == new_vp_children
    assert new_q_parent == terminals[-2].parent
    assert new_labels_test == [node.data['label'] for node in
                               trees.preorder(cont_tree)]


def test_punctuation_root(discont_tree, cont_tree):
    """transform.punctuation_root
    """
    terms = trees.terminals(discont_tree)
    terms[0].data['word'] = ","
    old_p = terms[0].parent
    assert len(trees.children(old_p)) == 2
    discont_tree = transform.punctuation_root(discont_tree)
    assert len(trees.children(old_p)) == 1
    assert terms[0].parent == discont_tree
    terms = trees.terminals(cont_tree)
    terms[3].data['word'] = ","
    old_p = terms[3].parent
    assert len(trees.children(old_p)) == 3
    cont_tree = transform.punctuation_root(cont_tree)
    assert len(trees.children(old_p)) == 2
    assert terms[3].parent == cont_tree


def test_ptb_delete_traces(cont_tree):
    """transform.ptb_delete_traces
    """
    terms = trees.terminals(cont_tree)
    terms[-2].data['label'] = "-NONE-"
    cont_tree = transform.ptb_delete_traces(cont_tree)
    assert len(trees.terminals(cont_tree)) == len(terms) - 1


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
