"""
treetools: Tools for transforming treebank trees.

This module provides basic data structures and functions for handling trees.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function
import itertools
import sys
from copy import deepcopy
from collections import namedtuple


# separators in labels
DEFAULT_GF_SEPARATOR = u"-"
DEFAULT_COINDEX_SEPARATOR = u"-"
DEFAULT_GAPPING_SEPARATOR = u"="
# character constants
# ... all kinds of brackets
OPENING_BRACKETS = {"(" : "LRB", "-LRB-" : "LRB",
                    "[" : "LSB", "-LSB-" : "LSB",
                    "{" : "LCB", "-LCB-" : "LCB"}
CLOSING_BRACKETS = {")" : "RRB", "-RRB-" : "RRB",
                    "]" : "RSB", "-RSB-" : "RSB",
                    "}" : "RCB", "-RCB-" : "RCB"}
BRACKETS = dict(list(OPENING_BRACKETS.items()) +\
                list(CLOSING_BRACKETS.items()))
# ... other stuff
QUOTES = [u"\"", u"'", u"''", u"`", u"``"]
COMMA = [u".", u",", u";", u"?", u"!", u"--", u":", u"-", u"/", u"..."]
PAIRPUNCT = QUOTES + list(BRACKETS.keys())
PUNCT = PAIRPUNCT + COMMA
# phrase brackets
PHRASE_BRACKETS = ["(", ")"]
# head marker
DEFAULT_HEAD_MARKER = u"'"
# fields and default values
NUMBER_OF_FIELDS = 6
FIELDS = ['word', 'lemma', 'label', 'morph', 'edge', 'parent_num']
DEFAULT_WORD = u""
DEFAULT_LEMMA = u"--"
DEFAULT_LABEL = u"EMPTY"
DEFAULT_MORPH = u"--"
DEFAULT_EDGE = u"--"
DEFAULT_ROOT = u"VROOT"

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
    newid = itertools.count()

    def __init__(self, data):
        """Construct a new tree and copy given data dict.
        """
        self.id = next(Tree.newid)
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

    def __hash__(self):
        return hash(self.id)


def make_node_data():
    """Make an empty node data and pre-initialize with fields
    """
    return dict(zip(FIELDS, [None] * NUMBER_OF_FIELDS))


def make_node_data_fill():
    """Make a node data hash, initialize with fields and fill them
    with default values.
    """
    fields = dict(zip(FIELDS, [None] * NUMBER_OF_FIELDS))
    fields['word'] = DEFAULT_WORD
    fields['lemma'] = DEFAULT_LEMMA
    fields['label'] = u"EMPTY"
    fields['morph'] = u"--"
    fields['edge'] = u"--"
    fields['parent_num'] = -1
    return fields


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


def unordered_terminals(tree):
    """Return all terminal children of this subtree.
    """
    if len(tree.children) == 0:
        return [tree]
    else:
        result = []
        for child in tree.children:
            result.extend(unordered_terminals(child))
        return result


def terminals(tree):
    """Return all terminal children of this subtree.
    """
    if len(tree.children) == 0:
        if not 'num' in tree.data:
            raise ValueError("no number in node data of terminal %s/%s" \
                             % (tree.data['word'], tree.data['label']))
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


def delete_terminal(tree, leaf):
    """Delete a leaf node and recursively all of its ancestors
    which do not have siblings. Root of the tree with the leaf
    must be given as well. Return the first node with siblings
    or the (given) root.
    """
    root = tree
    while not root.parent == None:
        root = root.parent
    terms = terminals(root)
    num = leaf.data['num']
    parent = leaf.parent
    while parent is not None and len(leaf.children) == 0:
        parent.children.remove(leaf)
        leaf = parent
        parent = leaf.parent
    # shift numbering
    for terminal in terms:
        if terminal.data['num'] > num:
            terminal.data['num'] -= 1
    return leaf


def right_sibling(tree):
    """Return the right sibling of this tree if it exists and None otherwise.
    """
    if tree.parent is None:
        return None
    siblings = children(tree.parent)
    for (index, sibling) in enumerate(siblings[:-1]):
        if sibling == tree:
            return siblings[index + 1]
    return None


def left_sibling(tree):
    """Return the left sibling of this tree if it exists and None otherwise.
    """
    if tree.parent is None:
        return None
    siblings = children(tree.parent)
    for (index, sibling) in enumerate(siblings[1:]):
        if sibling == tree:
            return siblings[index]
    return None


def lca(tree_a, tree_b):
    """Return the least common ancestor of two trees and None if there
    is none.
    """
    dom_a = [tree_a]
    parent = tree_a
    while not parent.parent is None:
        parent = parent.parent
        dom_a.append(parent)
    dom_b = [tree_b]
    parent = tree_b
    while not parent.parent is None:
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
    yield parent
    while not parent.parent is None:
        parent = parent.parent
        yield parent


def levels(tree):
    """Compute levels of all nodes (height).
    """
    levels = {}
    reverse_levels = {}
    for subtree in preorder(tree):
        if has_children(subtree):
            level = 0
            for terminal in terminals(subtree):
                path_length = 0
                path_element = terminal
                while not path_element == subtree:
                    path_element = path_element.parent
                    path_length += 1
                level = max(level, path_length)
            if level not in levels:
                levels[level] = []
            levels[level].append(subtree)
            reverse_levels[subtree] = level
    return levels, reverse_levels

            
def get_label(tree, **params):
    """Compute subtree label decorations depending on given parameters.
    """
    label = tree.data['label']
    gf_separator = DEFAULT_GF_SEPARATOR
    if 'gf_separator' in params:
        gf_separator = unicode(params['gf_separator'])
    gf_string = ""
    if 'gf' in params and not tree.data['edge'].startswith("-") \
       and (has_children(tree)
            or 'gf_terminals' in params):
        gf_string = "%s%s" % (gf_separator, tree.data['edge'])
    head = ""
    if 'mark_heads_marking' in params and tree.data['head']:
        head = DEFAULT_HEAD_MARKER
    split_marker = ""
    if 'boyd_split_marking' in params and tree.data['split']:
        split_marker = "*"
    split_number = ""
    if 'boyd_split_numbering' in params and tree.data['split']:
        split_number = tree.data['block_number']
    return u"%s%s%s%s%s" % (label, gf_string, head, split_marker, split_number)


class Label(object):
    """Dummy class for labels
    """
    def __str__(self):
        result = ""
        for element in self.__dict__:
            result += element + " -> " + str(self.__dict__[element]) + "\n"
        return result


def parse_label(label, **params):
    """Generic parsing of treebank label assuming following
    format (no spaces):

    LABEL (GF_SEP GF)? (GAPINDEX_SEP GAPINDEX)? (COINDEX_SEP COINDEX)?
    HEADMARKER?

    LABEL: \S+, GF_SEP: [#\-], GF: [^\-\=#\s]+
    COINDEX_SEP: \-, GAPINDEX_SEP: \=, CO/GAPINDEX: \d+

    Single parts are returned as namedtuple. Non-presented parts
    are returned with default values from tree.py (or empty).
    """
    gf_separator = DEFAULT_GF_SEPARATOR
    if gf_separator in params:
        gf_separator = params['gf_separator']
    # start from the back
    # head marker
    headmarker = ""
    if len(label) > 0 and label[-1] == DEFAULT_HEAD_MARKER:
        headmarker = label[-1]
        label = label[:-1]
    # coindex or gapping sep (PTB)
    coindex = ""
    coindex_sep_pos = label.rfind(DEFAULT_COINDEX_SEPARATOR)
    if coindex_sep_pos > -1:
        if label[coindex_sep_pos + 1:].isdigit():
            coindex = label[coindex_sep_pos + 1:]
            label = label[:coindex_sep_pos]
    gapindex = ""
    gapping_sep_pos = label.rfind(DEFAULT_GAPPING_SEPARATOR)
    if gapping_sep_pos > -1:
        if label[gapping_sep_pos + 1:].isdigit():
            gapindex = label[gapping_sep_pos + 1:]
            label = label[:gapping_sep_pos]
    # gf
    gf = DEFAULT_EDGE
    gf_sep_pos = -1
    for i, char in list(enumerate(label)):
        # first separator from left to right counts
        # TODO for TueBa-D/Z this should be right to left
        if char == gf_separator:
            gf_sep_pos = i
            break
    if gf_sep_pos > 0 and gf_sep_pos < len(label) - 1:
        gf = label[gf_sep_pos + 1:]
        label = label[:gf_sep_pos]
    if len(gf) == 0:
        gf = DEFAULT_EDGE
    if len(label) == 0:
        label = DEFAULT_LABEL
    # is trace?
    is_trace = len(label) > 0 and label[0] == '*' and label[-1] == '*'
    lab = Label()
    lab.label = label
    lab.gf = gf
    lab.gf_separator = gf_separator
    lab.coindex = coindex
    lab.gapindex = gapindex
    lab.headmarker = headmarker
    lab.is_trace = is_trace
    return lab


def format_label(label, **params):
    """Glue parts of parsed label (parse_label) together. To delete a certain
    component of the label, parse_label it, set the corresponding components
    to the empty string and then format_label it.
    If param always_label is given, we also write the label if label == trees.
    DEFAULT_LABEL. Same for gf and DEFAULT_EDGE.
    """
    label_always = 'always_label' in params
    edge_always = 'always_gf' in params
    lab = ""
    if not label.label == DEFAULT_LABEL or label_always:
        lab = label.label
    index = ""
    if len(label.gapindex) > 0:
        index += DEFAULT_GAPPING_SEPARATOR + label.gapindex
    if len(label.coindex) > 0:
        index += DEFAULT_COINDEX_SEPARATOR + label.coindex
    gf = ""
    if not label.gf == DEFAULT_EDGE or edge_always:
        gf = label.gf_separator + label.gf
    headmarker = "'" if label.headmarker else ""
    result = lab + gf + index + headmarker
    return result


def replace_chars(tree, cands):
    """Replace characters in node data before bracketing output given a
    dictionary.
    """
    thestringtype = None
    if sys.version_info[0] < 3:
        thestringtype = basestring
    else:
        thestringtype = str
    for field in FIELDS:
        if not tree.data[field] is None \
                and isinstance(tree.data[field], thestringtype):
            for cand in cands:
                tree.data[field] = tree.data[field].replace(cand, cands[cand])
    return tree
