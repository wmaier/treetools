from . import trees

def tracelabels_to_preterminals(tree, **params):
    """Label all terminal nodes labeled "-NONE-" with the
    respective word (which should be a trace label).

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    for terminal in trees.terminals(tree):
        if terminal.data['label'] == "-NONE-":
            terminal.data['label'] = terminal.data['word']
            terminal.data['word'] = "EPSILON"
    return tree


def tracelabels_to_none(tree, **params):
    """Label all terminal nodes labeled "-NONE-" with the
    respective word (which should be a trace label).

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    for terminal in trees.terminals(tree):
        if terminal.data['label'] == "-NONE-":
#            terminal.data['label'] = terminal.data['word']
            terminal.data['word'] = "-NONE-"
    return tree


def punct_to_eps(tree, **params):
    """Rename all preterminals where the words are punctuation
    to -PUNCT-
    """
    for terminal in trees.terminals(tree):
        if terminal.data['word'] in trees.C_PUNCT:
            terminal.data['label'] == "-PUNCT-"
    return tree


def ptb_transform(tree, **params):
    """Delete PTB traces.
    """
    tree = tracelabels_to_none(tree, **params)
    params['delete_traces'] = '-NONE-'
    tree = delete_traces(tree, **params)
    for node in trees.preorder(tree):
        label = trees.parse_label(node.data['label'])
        label.coindex = ""
        node.data['label'] = trees.format_label(label)
    return tree


def ptb_punct_to_root(tree, **params):
    terms = trees.terminals(tree)
    punct = [terminal for terminal in terms
             if terminal.data['label'] in trees.C_PUNCT \
             and len(trees.children(terminal.parent)) > 1]
    for p in punct:
        p.parent.children.remove(p)
        tree.children.append(p)
        p.parent = tree
    return tree
