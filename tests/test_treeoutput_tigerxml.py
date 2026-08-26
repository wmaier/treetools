"""Focused tests for TIGERXML output."""

from io import StringIO

from treetools import treeoutput, trees


def test_tigerxml_omits_missing_terminal_fields():
    root = trees.Tree(trees.make_node_data())
    root.data['label'] = trees.DEFAULT_ROOT
    root.data['sid'] = 1
    terminal = trees.Tree(trees.make_node_data())
    terminal.data['word'] = 'word'
    terminal.data['label'] = 'NN'
    terminal.data['edge'] = trees.DEFAULT_EDGE
    terminal.data['num'] = 1
    terminal.parent = root
    root.children.append(terminal)
    output = StringIO()

    treeoutput.tigerxml(root, output)

    xml = output.getvalue()
    assert 'word="word"' in xml
    assert 'pos="NN"' in xml
    assert 'lemma=' not in xml
    assert 'morph=' not in xml
