C_QUOTES = [u"\"", u"'", u"''", u"`", u"``"]
C_COMMA = [u".", u",", u";", u"?", u"!", u"--", u":", u"-", u"/", u"..."]
C_OPENING_PARENS = [u"(", u"[", u"{", u"-LRB-", u"LRB"]
C_CLOSING_PARENS = [u")", u"]", u"}", u"-RRB-", u"RRB"]
C_PARENS = C_OPENING_PARENS + C_CLOSING_PARENS
C_PAIRPUNCT = C_QUOTES + C_PARENS
C_PUNCT = C_PAIRPUNCT + C_COMMA
DEFAULT_LABEL = u"LABEL"


def delete_terminal(tree, leaf):
    """Delete a leaf node and recursively all of its ancestors
    which do not have siblings. Root of the tree with the leaf
    must be given as well. Return the first node with siblings
    or the (given) root.
    """
    num = leaf.data['num']
    parent = leaf.parent
    while parent is not None and len(leaf.children) == 0:
        parent.children.remove(leaf)
        leaf = parent
        parent = leaf.parent
    # shift numbering
    for terminal in terminals(tree):
        if terminal.data['num'] > num:
            terminal.data['num'] -= 1
    return parent


def delete_terminal_single(tree, leaf):
    """Delete a leaf node. Possibly leaves unnumbered leaf
    nodes back.
    """
    num = leaf.data['num']
    parent = leaf.parent
    if parent is not None:
        parent.children.remove(leaf)
    # shift numbering (skip unnumbered nodes)
    for terminal in unordered_terminals(tree):
        if 'num' in terminal.data and terminal.data['num'] > num:
            terminal.data['num'] -= 1
    return parent
