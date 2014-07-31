
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
