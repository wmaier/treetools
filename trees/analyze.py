""" 
treetools: Tools for transforming treebank trees.

This module provides functions for analyzing trees.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from . import trees


def gap_degree(tree):
    """Return the maximal gap degree of any node of the given tree.
    """
    result = 0
    for subtree in trees.preorder(tree):
        gap_deg = 0
        terms = trees.terminals(subtree)
        for i, _ in enumerate(terms[:-1]):
            if terms[i]['num'] + 1 < terms[i + 1]['num']:
                gap_deg += 1
        result = max(result, gap_deg)
    return result


def is_discontinuous(tree):
    """Return True iff this tree contains at least one discontinuous node.
    """
    for subtree in trees.preorder(tree):
        terms = trees.terminals(subtree)
        for i, _ in enumerate(terms[:-1]):
            if terms[i]['num'] + 1 < terms[i + 1]['num']:
                return True
    return False
