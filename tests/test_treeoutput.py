"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
import tempfile
import sys
from io import StringIO
from trees import treeinput, treeoutput, transform, treeanalysis
from . import testdata


def test_export(discont_tree):
    s = StringIO()
    treeoutput.export(discont_tree, s)
    output = []
    for l in s.getvalue().split("\n"):
        output.append(l)
    print(output)
    assert output == testdata.SAMPLE_EXPORT_OUTPUT


def test_brackets(cont_tree):
    s = StringIO()
    treeoutput.brackets(cont_tree, s)
    output = s.getvalue()
    assert output.strip() == testdata.SAMPLE_BRACKETS_OUTPUT.strip()
    s = StringIO()
    params = {'brackets_emptyroot' : True}
    treeoutput.brackets(cont_tree, s, **params)
    output = s.getvalue()
    assert output.strip() == testdata.SAMPLE_BRACKETS_OUTPUT_NOROOT.strip()


def test_brackets(cont_tree, discont_tree):
    s = StringIO()
    treeoutput.discobrackets(cont_tree, s)
    output = s.getvalue()
    assert output.strip() == testdata.SAMPLE_DISCOBRACKETS_OUTPUT_CONT.strip()
    s = StringIO()
    treeoutput.discobrackets(discont_tree, s)
    output = s.getvalue()
    print(output)
    assert output.strip() == testdata.SAMPLE_DISCOBRACKETS_OUTPUT_DISCONT.strip()


def test_terminals(discont_tree):
    s = StringIO()
    treeoutput.terminals(discont_tree, s)
    output = s.getvalue().split()
    assert output == testdata.WORDS
    s = StringIO()
    params = {'pos_only' : True}
    treeoutput.terminals(discont_tree, s, **params)
    output = s.getvalue().split()
    assert output == testdata.POS
    s = StringIO()
    params = {'terminals_one' : True}
    treeoutput.terminals(discont_tree, s, **params)
    output = s.getvalue().strip().split("\n")
    assert output == testdata.WORDS
    s = StringIO()
    params = {'terminals_one' : True, 'pos_only': True}
    treeoutput.terminals(discont_tree, s, **params)
    output = s.getvalue().strip().split("\n")
    assert output == testdata.POS


def test_begin_end():
    s = StringIO()
    treeoutput.export_begin(s)
    treeoutput.export_end(s)
    treeoutput.brackets_begin(s)
    treeoutput.brackets_end(s)
    treeoutput.discobrackets_begin(s)
    treeoutput.discobrackets_end(s)
    treeoutput.terminals_begin(s)
    treeoutput.terminals_end(s)
    treeoutput.tigerxml_begin(s)
    treeoutput.tigerxml_end(s)
    assert s.getvalue() == "<?xml version='1.0'?>\n<corpus>\n<body>\n</body>\n</corpus>"


def test_parse_split_specification():
    s = "rest_20%_5000#"
    spec = treeoutput.parse_split_specification(s, 10000)
    assert spec == [3000, 2000, 5000]
    