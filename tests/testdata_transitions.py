"""
treetools: Tools for transforming treebank trees.

Unit tests constants for transition tests

Author: Wolfgang Maier <maierw@hhu.de>
"""

TRANS_TERMINALS = [('Who', 'WP'), ('did', 'VB'), ('Fritz', 'NNP'), (
    'tell', 'VB'), ('Hans', 'NNP'), ('that', 'IN'), ('Manfred', 'NNP'), ('likes', 'VB'), ('?', '?')]
TRANS_CONT_TOPDOWN_NEGRAHEADS_TRANSITIONS = ["SHIFT", "SHIFT", "UNARY-VP", "SHIFT", "UNARY-NP", "SHIFT", "BINARY-LEFT-@SBAR", "BINARY-LEFT-SBAR", "SHIFT",
                                             "SHIFT", "BINARY-LEFT-@VP", "BINARY-LEFT-VP", "SHIFT", "SHIFT", "SHIFT", "BINARY-LEFT-@S", "BINARY-LEFT-@S", "BINARY-LEFT-S", "BINARY-LEFT-VROOT"]
TRANS_DISCONT_GAP_TRANSITIONS = ["SHIFT", "SHIFT", "SHIFT", "RLEFT-@S", "SHIFT", "SHIFT", "RLEFT-@VP", "SHIFT", "SHIFT", "UNARY-NP",
                                 "RLEFT-@SBAR", "SHIFT", "GAP", "GAP", "GAP", "RRIGHT-VP", "GAP", "GAP", "RLEFT-SBAR", "RLEFT-VP", "RLEFT-S", "SHIFT", "RLEFT-VROOT"]
