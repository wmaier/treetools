"""
treetools: Tools for transforming treebank trees.

This module provides basic data structures and functions for handling trees.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function
import itertools
from copy import deepcopy
from collections import namedtuple


# separators in labels
DEFAULT_GF_SEPARATOR = u"-"
DEFAULT_COINDEX_SEPARATOR = u"-"
DEFAULT_GAPPING_SEPARATOR = u"="
# brackets related stuff
# ... allowed as phrase brackets
PHRASE_BRACKETS = ["(", ")"]
# ... all kinds of brackets
BRACKETS = {"(" : "LRB", ")" : "RRB",
            "[" : "LSB", "]" : "RSB",
            "{" : "LCB", "}" : "RCB"}
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


def right_sibling(tree):
    """Return the right sibling of this tree if it exists and None otherwise.
    """
    if tree.parent is None:
        return None
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


def parse_label(label, **params):
    """Generic parsing of treebank label assuming following 
    format (no spaces):

    LABEL (GF_SEP GF)? ((COINDEX_SEP COINDEX)|(GAPINDEX_SEP GAPINDEX))? 
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
        headmarker = True
        label = label[:-1]
    # coindex or gapping sep (PTB)
    coindex = ""
    gapindex = ""
    coindex_sep_pos = None
    gapping_sep_pos = None
    for i, char in reversed(list(enumerate(label))):
        if char == DEFAULT_COINDEX_SEPARATOR and coindex_sep_pos == None:
            coindex_sep_pos = i
        if char == DEFAULT_GAPPING_SEPARATOR and gapping_sep_pos == None:
            gapping_sep_pos = i
    if coindex_sep_pos is not None and label[coindex_sep_pos + 1:].isdigit():
        coindex = label[coindex_sep_pos + 1:]
        label = label[:coindex_sep_pos]
    if gapping_sep_pos is not None and label[gapping_sep_pos + 1:].isdigit() \
       and coindex == "":
        gapindex = label[gapping_sep_pos + 1:]
        label = label[:gapping_sep_pos]
    # gf
    gf = DEFAULT_EDGE
    gf_sep_pos = None
    for i, char in reversed(list(enumerate(label))):
        # first separator from right to left counts
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
    Label = namedtuple('Label', 'label gf gf_separator coindex gapindex ' \
                       'headmarker is_trace')
    return Label(label, gf, gf_separator, coindex, gapindex, headmarker, is_trace)


def format_label(label, **params):
    """Glue parts of parsed label (parse_label) together. To delete a certain
    component of the label, parse_label it, set the corresponding components
    to the empty string and then format_label it.
    If param always_label is given, we also write the label if label == trees.
    DEFAULT_LABEL. Same for gf and DEFAULT_EDGE.
    """
    label_always = 'always_label' in params
    edge_always = 'always_gf' in params
    if len(label.gapindex) > 0 and len(label.coindex) > 0:
        raise ValueError("Cannot have gapping index and coindex on same label")
    lab = ""
    if not label.label == DEFAULT_LABEL or label_always:
        lab = label.label
    index = ""
    if len(label.coindex) > 0:
        index = DEFAULT_COINDEX_SEPARATOR + label.coindex
    elif len(label.gapindex) > 0:
        index = DEFAULT_GAPPING_SEPARATOR + label.gapindex
    gf = ""
    if not label.gf == DEFAULT_EDGE or edge_always:
        gf = label.gf_separator + label.gf
    headmarker = "'" if label.headmarker else ""
    return lab + gf + index + headmarker


def replace_chars(tree, cands):
    """Replace characters in node data before bracketing output given a 
    dictionary.
    """
    for field in FIELDS:
        if not tree.data[field] is None \
                and isinstance(tree.data[field], basestring):
            for cand in cands:
                tree.data[field] = tree.data[field].replace(cand, cands[cand])
    return tree
