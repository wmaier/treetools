"""
treetools: Tools for transforming treebank trees.

Unit tests constants for transition tests

Author: Wolfgang Maier <maierw@hhu.de>
"""

TRANS_TERMINALS = [('Who', 'WP'), ('did', 'VB'), ('Fritz', 'NNP'), (
    'tell', 'VB'), ('Hans', 'NNP'), ('that', 'IN'), ('Manfred', 'NNP'), ('likes', 'VB'), ('?', '?')]
TRANS_CONT_TOPDOWN_NEGRAHEADS_TRANSITIONS = ["SHIFT", "SHIFT", "UNARY-VP", "SHIFT", "UNARY-NP", "SHIFT", "BINARY-LEFT-@SBAR", "BINARY-LEFT-SBAR", "SHIFT",
                                             "SHIFT", "BINARY-LEFT-@VP", "BINARY-LEFT-VP", "SHIFT", "SHIFT", "SHIFT", "BINARY-LEFT-@S", "BINARY-LEFT-@S", "BINARY-LEFT-S", "BINARY-LEFT-VROOT"]
TRANS_DISCONT_GAP_TRANSITIONS = ["SHIFT", "SHIFT", "SHIFT", "R-LEFT-@S", "SHIFT", "SHIFT", "R-LEFT-@VP", "SHIFT", "SHIFT", "UNARY-NP",
                                 "R-LEFT-@SBAR", "SHIFT", "GAP", "GAP", "GAP", "R-RIGHT-VP", "GAP", "GAP", "R-LEFT-SBAR", "R-LEFT-VP", "R-LEFT-S", "SHIFT", "R-LEFT-VROOT"]
