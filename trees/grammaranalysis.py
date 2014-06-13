"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for analyzing grammars.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from collections import Counter


def fan_out(lin):
    """Given a function and the corresponding lineratization,
    return an array with the fan-out of each non-terminal in the
    given function.
    """
    cnt = Counter([rhsref + 1 for arg in lin for (rhsref, _) in arg])
    result = [None] * (len(cnt) + 1)
    for i in cnt:
        result[i] = cnt[i]
    result[0] = len(lin)
    return result


def is_contextfree(grammar):
    """Return true iff the given grammar is context-free.
    """
    for func in grammar:
        for lin in grammar[func]:
            if fan_out(lin)[0] > 1:
                return False
    return True
