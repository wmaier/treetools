import unittest
import tempfile
import os
from StringIO import StringIO
from . import trees, treeinput

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

class DiscontTreeTests(unittest.TestCase):

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.tempfile_name = temp.name
            temp.write(EXPORT_SAMPLE)
            temp.flush()
        reader = treeinput.export(self.tempfile_name, 'utf8')
        self.tree = reader.next()
        self.preorder_labels = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                                u'VB', u'IN', u'NP', u'NNP', u'VB', u'NNP',
                                u'VB', u'NNP', u'?']
        self.preorder_words = [None, u'#504', u'#503', u'#502', u'#501',
                               u'Who', u'likes', u'that', u'#500', u'Manfred',
                               u'tell', u'Hans', u'did', u'Fritz', u'?']

    def test_terminals(self):
        terms = trees.terminals(self.tree)
        self.assertEqual(len(terms), 9)

    def test_nodes(self):
        nodes = [node for node in trees.preorder(self.tree)]
        self.assertEqual(len(nodes), 15)
        labels = [node.data['label'] for node in nodes]
        words = [node.data['word'] for node in nodes]
        self.assertTrue(all([a == b for (a,b) in zip(labels, 
                                                     self.preorder_labels)]))
        self.assertTrue(all([a == b for (a,b) in zip(words,
                                                     self.preorder_words)]))

    def tearDown(self):
        os.remove(self.tempfile_name)


if __name__ == '__main__':
    unittest.main()
