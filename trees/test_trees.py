"""
treetools: Tools for transforming treebank trees.

Unit tests

Author: Wolfgang Maier <maierw@hhu.de>
"""
import unittest
import tempfile
import os
import sys
import copy
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
WORDS = [ u'Who', u'did', u'Fritz',  u'tell', u'Hans', 
          u'that', u'Manfred', u'likes', u'?']
PREORDER_LABELS = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                   u'VB', u'IN', u'NP', u'NNP', u'VB', u'NNP',
                   u'VB', u'NNP', u'?']
PREORDER_LABELS_BOYD = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', 
                        u'WP', u'VB', u'NNP', u'VP', u'VB', 
                        u'NNP', u'SBAR', u'IN', u'NP', u'NNP', 
                        u'VP', u'VB', u'?'] 
PREORDER_LABELS_RAISING = [u'VROOT', u'S', u'WP', u'VB', u'NNP', 
                           u'VP', u'VB', u'NNP', u'SBAR', u'IN', 
                           u'NP', u'NNP', u'VP', u'VB', u'?']


class ContTreeTests(unittest.TestCase):

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.brackets_tempfile_name = temp.name
            temp.write(BRACKETS_SAMPLE)
            temp.flush()
        params = {}
        bracketsreader = treeinput.brackets(self.brackets_tempfile_name, 
                                        'utf8', **params)
        self.tree = bracketsreader.next()
        
    def test_nodes(self):
        terms = trees.terminals(self.tree)
        self.assertEqual(len(terms), 9)
        nodes = [node for node in trees.preorder(self.tree)]
        self.assertEqual(len(nodes), 15)
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in terms]
        self.assertEqual(labels, PREORDER_LABELS_RAISING)
        self.assertEqual(words, WORDS)

    def tearDown(self):
        os.remove(self.brackets_tempfile_name)


class DiscontTreeTests(object):

    def test_nodes(self):
        terms = trees.terminals(self.tree)
        nodes = [node for node in trees.preorder(self.tree)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in terms]
        self.assertEqual(len(terms), 9)
        self.assertEqual(len(nodes), 15)
        self.assertEqual(labels, PREORDER_LABELS)
        self.assertEqual(words, WORDS)

    def test_root_attach(self):
        terms = trees.terminals(self.tree_root_attach)
        nodes = [node for node in trees.preorder(self.tree_root_attach)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in terms]
        self.assertEqual(labels, PREORDER_LABELS)
        self.assertEqual(words, WORDS)
        self.assertRaises(ValueError, transform.boyd_split, self.tree_root_attach)

    def test_boyd(self):
        terms = trees.terminals(self.tree_boyd)
        nodes = [node for node in trees.preorder(self.tree_boyd)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in terms]
        self.assertEqual(labels, PREORDER_LABELS_BOYD)
        self.assertEqual(words, WORDS)

    def test_raising(self):
        terms = trees.terminals(self.tree_raising)
        nodes = [node for node in trees.preorder(self.tree_raising)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in terms]
        self.assertEqual(labels, PREORDER_LABELS_RAISING)
        self.assertEqual(words, WORDS)


class ExportFormatTests(unittest.TestCase, DiscontTreeTests):

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.export_tempfile_name = temp.name
            temp.write(EXPORT_SAMPLE)
            temp.flush()
        params = {}
        exportreader = treeinput.export(self.export_tempfile_name, 
                                        'utf8', **params)
        self.tree = exportreader.next()
        self.tree_root_attach = copy.deepcopy(self.tree)
        self.tree_root_attach = transform.root_attach(self.tree_root_attach)
        self.tree_negra_mark_heads = copy.deepcopy(self.tree_root_attach)
        self.tree_negra_mark_heads = transform.negra_mark_heads(self.tree_negra_mark_heads)
        self.tree_boyd = copy.deepcopy(self.tree_negra_mark_heads)
        self.tree_boyd = transform.boyd_split(self.tree_boyd)
        self.tree_raising = copy.deepcopy(self.tree_boyd)
        self.tree_raising = transform.raising(self.tree_raising)

    def tearDown(self):
        os.remove(self.export_tempfile_name)


class TigerxmlFormatTests(unittest.TestCase, DiscontTreeTests):

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.tigerxml_tempfile_name = temp.name
            temp.write(TIGERXML_SAMPLE)
            temp.flush()
        params = {}
        tigerxmlreader = treeinput.tigerxml(self.tigerxml_tempfile_name, 
                                        'utf8', **params)
        self.tree = tigerxmlreader.next()
        self.tree_root_attach = copy.deepcopy(self.tree)
        self.tree_root_attach = transform.root_attach(self.tree_root_attach)
        self.tree_negra_mark_heads = copy.deepcopy(self.tree_root_attach)
        self.tree_negra_mark_heads = transform.negra_mark_heads(self.tree_negra_mark_heads)
        self.tree_boyd = copy.deepcopy(self.tree_negra_mark_heads)
        self.tree_boyd = transform.boyd_split(self.tree_boyd)
        self.tree_raising = copy.deepcopy(self.tree_boyd)
        self.tree_raising = transform.raising(self.tree_raising)

    def tearDown(self):
        os.remove(self.tigerxml_tempfile_name)


if __name__ == '__main__':
    unittest.main()
