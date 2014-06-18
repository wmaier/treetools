import unittest
import tempfile
import os
from StringIO import StringIO
from . import trees, treeinput, transform


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
?			?(	--		--	0
#500			NP=X	--		--	502
#501			VP	--		--	502
#502			SBAR	--		--	503
#503			VP	--		--	504
#504			S	--		--	0
#EOS 1
"""
PREORDER_LABELS = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                   u'VB', u'IN', u'NP', u'NNP', u'VB', u'NNP',
                   u'VB', u'NNP', u'?LRB']
PREORDER_WORDS = [None, u'#504', u'#503', u'#502', u'#501',
                  u'Who', u'likes', u'that', u'#500', u'Manfred',
                  u'tell', u'Hans', u'did', u'Fritz', u'?']
PREORDER_LABELS_BOYD = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', 
                        u'WP', u'VB', u'NNP', u'VP', u'VB', 
                        u'NNP', u'SBAR', u'IN', u'NP', u'NNP', 
                        u'VP', u'VB', u'?LRB'] 
PREORDER_WORDS_BOYD = [None, u'#504', u'#503', u'#502', u'#501', 
                       u'Who', u'did', u'Fritz', u'#503', u'tell', 
                       u'Hans', u'#502', u'that', u'#500', 
                       u'Manfred', u'#501', u'likes', u'?']


class DiscontTreeTests(unittest.TestCase):

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.export_tempfile_name = temp.name
            temp.write(EXPORT_SAMPLE)
            temp.flush()
        params = {'replace_parens' : True, 'trunc_equals' : True}
        exportreader = treeinput.export(self.export_tempfile_name, 
                                        'utf8', **params)
        self.tree = exportreader.next()
        self.tree_root_attach = transform.root_attach(self.tree)
        self.tree_boyd = transform.negra_mark_heads(self.tree_root_attach)
        self.tree_boyd = transform.boyd_split(self.tree_boyd)
        self.tree_raising = transform.raising(self.tree_boyd)

    def test_nodes(self):
        terms = trees.terminals(self.tree)
        self.assertEqual(len(terms), 9)
        nodes = [node for node in trees.preorder(self.tree)]
        self.assertEqual(len(nodes), 15)
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in nodes]
        print labels
        print PREORDER_LABELS
        sys.exit()
        self.assertTrue(all([a == b for (a,b) in zip(labels, 
                                                     PREORDER_LABELS)]))
        self.assertTrue(all([a == b for (a,b) in zip(words,
                                                     PREORDER_WORDS)]))

    def test_root_attach(self):
        terms = trees.terminals(self.tree_root_attach)
        self.assertEqual(len(terms), 9)
        nodes = [node for node in trees.preorder(self.tree_root_attach)]
        self.assertEqual(len(nodes), 15)
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in nodes]
        print labels
        self.assertTrue(all([a == b for (a,b) in zip(labels, 
                                                     PREORDER_LABELS)]))
        self.assertTrue(all([a == b for (a,b) in zip(words,
                                                     PREORDER_WORDS)]))

    def test_boyd(self):
        nodes = [node for node in trees.preorder(self.tree_boyd)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in nodes]
        self.assertTrue(all([a == b for (a,b) in zip(labels, 
                                                     PREORDER_LABELS_BOYD)]))
        self.assertTrue(all([a == b for (a,b) in zip(words,
                                                     PREORDER_WORDS_BOYD)]))

    def test_raising(self):
        nodes = [node for node in trees.preorder(self.tree_raising)]
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in nodes]
        print words

    def tearDown(self):
        os.remove(self.export_tempfile_name)


if __name__ == '__main__':
    unittest.main()
