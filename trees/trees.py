""" 
treetools: Tools for transforming treebank trees.

This module provides basic data structures and functions for handling trees. 

Author: Wolfgang Maier <maierw@hhu.de>
"""
import itertools
from copy import deepcopy


DEFAULT_GF_SEPARATOR = u"-"
DEFAULT_COINDEX_SEPARATOR = u"-"
DEFAULT_LEMMA = u"--"
DEFAULT_EDGE = u"--"
DEFAULT_MORPH = u"--"
DEFAULT_HEAD_MARKER = u"'"
NUMBER_OF_FIELDS = 6
FIELDS = ['word', 'lemma', 'label', 'morph', 'edge', 'parent_num']


class Tree(object):
    """A tree is represented by a unique ID per instance, a parent, a
    children list, and a data dict. New instances are constructed by
    copying given data dict. If there are no children, there must be a
    num key in the data dict which denotes the position
    index. Repeated or unspecified indices are an error. Note that
    comparison between Trees is done solely on the basis of the unique
    ID. 
    """
    # unique id generator
    newid = itertools.count().next
    
    def __init__(self, data):
        """Construct a new tree and copy given data dict.
        """
        self.id = Tree.newid()
        self.children = []
        self.parent = None
        self.data = deepcopy(data)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


def make_node_data():
    """Make an empty node data and pre-initialize with fields
    """
    return dict(zip(FIELDS, [None] * NUMBER_OF_FIELDS))


def preorder(tree):
    """Generator which performs a preorder tree traversal and yields
    the subtrees encountered on its way.
    """
    yield tree
    for child in children(tree):
        for child_tree in preorder(child):
            yield child_tree


def postorder(tree):
    """Generator which performs a postorder tree traversal and yields
    the subtrees encountered on its way.
    """
    for child in children(tree):
        for child_tree in postorder(child):
            yield child_tree
    yield tree


def children(tree):
    """Return the ordered children of the root of this tree.
    """
    return sorted(tree.children, key=lambda x: terminals(x)[0].data['num'])


def has_children(tree):
    """Return true if this tree has any child.
    """
    return len(tree.children) > 0


def terminals(tree):
    """Return all terminal children of this subtree.
    """
    if len(tree.children) == 0:
        return [tree]
    else:
        result = []
        for child in tree.children:
            result.extend(terminals(child))
        return sorted(result, key=lambda x: x.data['num'])


def terminal_blocks(tree):
    """Return an array of arrays of terminals representing the 
    continuous blocks covered by the root of the tree given as
    argument."""
    blocks = [[]]
    terms = terminals(tree)
    for i, terminal in enumerate(terms[:-1]):
        blocks[-1].append(terminal)
        if terms[i].data['num'] + 1 < terms[i + 1].data['num']:
            blocks.append([])
    blocks[-1].append(terms[-1])
    return blocks


def right_sibling(tree):
    """Return the right sibling of this tree if it exists and None otherwise.
    """
    siblings = children(tree.parent)
    for (index, _) in enumerate(siblings[:-1]):
        if siblings[index] == tree:
            return siblings[index + 1]
    return None


def lca(tree_a, tree_b):
    """Return the least common ancestor of two trees and None if there 
    is none.
    """
    dom_a = [tree_a]
    parent = tree_a
    while not parent.parent == None:
        parent = parent.parent
        dom_a.append(parent)
    dom_b = [tree_b]
    parent = tree_b
    while not parent.parent == None:
        parent = parent.parent
        dom_b.append(parent)
    i = 0
    for i, (el_a, el_b) in enumerate(zip(dom_a[::-1], dom_b[::-1])):
        if not el_a == el_b:
            return dom_a[::-1][i - 1]
    return None


def dominance(tree):
    """Return all ancestors of this tree including the tree itself.
    """
    parent = tree
    while not parent.parent == None:
        yield parent
        parent = parent.parent
