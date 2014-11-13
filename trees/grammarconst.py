"""
treetools: Tools for transforming treebank trees.

grammar constants and utilities

Author: Wolfgang Maier <maierw@hhu.de>
"""

# PMCFG format constants
PRAGMA = ":"
RULE = ":"
RULEARROW = "<-"
LINEARIZATION = "="
SEQUENCE = "->"
# RCG format constants
RCG_RULEARROW = "-->"
# other constants
DEFAULT_BINLABEL = "@"
DEFAULT_BINSUFFIX = "X"
DEFAULT_MARKOV_HORIZONTALSEP = "-"
DEFAULT_MARKOV_VERTICALSEP = "^"
DEFAULT_VERT = "VERT"


def label_strip_fanout(label):
    """Assume the d+$ in a given label to be fanout and return
    the stripped version of the label.
    """
    while label[-1].isdigit():
        label = label[:-1]
    return label
