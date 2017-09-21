"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar output.

Author: Wolfgang Maier <maierw@hhu.de>
"""

import io


def plain(trans, dest, dest_enc, **params):
    """Write plain transitions.
    """
    with io.open(u"%s" % dest, 'w', encoding=dest_enc) as trans_stream:
        for seq in trans:
            trans_stream.write(u"%s\n" % ' '.join([u"%s" % t.pretty_print() for t in seq]))


FORMATS = [plain]
FORMAT_OPTIONS = {}
