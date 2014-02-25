""" 
treetools: Tools for transforming treebank trees.

This module provides basic data structures and functions for 
handling trees. A single (sub)tree is represented by a dict 
with obligatory keys data, children, parent. We do not rely 
on the children to be ordered. The function children() can be 
used to get an ordered list of children ordered by the 
respective leftmost terminal they dominate. If there are no 
children, there must be a num key which denotes the position 
index. Repeated or unspecified indices are an error. Missing 
children or parent keys are also an error too (use 
make_tree()).

Author: Wolfgang Maier <maierw@hhu.de>
"""
from copy import deepcopy


def make_tree(data):
    """Make an empty tree and possibly initialize with given data.
    """
    # make a copy of given data and make sure to overwrite
    # children and parent 
    return dict(deepcopy(data), **{ 'children' : [], 'parent' : None} )


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
    return sorted(tree['children'], key=lambda x: terminals(x)[0]['num'])


def has_children(tree):
    """Return true if this tree has any child.
    """
    return len(tree['children']) > 0


def terminals(tree):
    """Return all terminal children of this subtree.
    """
    if len(tree['children']) == 0:
        return [tree]
    else:
        result = []
        for child in tree['children']:
            result.extend(terminals(child))
        return sorted(result, key=lambda x: x['num'])


def terminal_blocks(tree):
    """Return an array of arrays of terminals representing the 
    continuous blocks covered by the root of the tree given as
    argument."""
    blocks = [[]]
    terms = terminals(tree)
    for i, terminal in enumerate(terms[:-1]):
        blocks[-1].append(terminal)
        if terms[i]['num'] + 1 < terms[i + 1]['num']:
            blocks.append([])
    blocks[-1].append(terms[-1])
    return blocks


def right_sibling(tree):
    """Return the right sibling of this tree if it exists and None otherwise.
    """
    siblings = children(tree['parent'])
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
    while not parent['parent'] == None:
        parent = parent['parent']
        dom_a.append(parent)
    dom_b = [tree_b]
    parent = tree_b
    while not parent['parent'] == None:
        parent = parent['parent']
        dom_b.append(parent)
    i = 0
    for i, (el_a, el_b) in enumerate(zip(dom_a[::-1], dom_b[::-1])):
        if not el_a == el_b:
            return dom_a[::-1][i - 1]
    return None

