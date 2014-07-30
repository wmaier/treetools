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


def symetrify(tree):
    """Reattach pairwise punctuation symetrically. A punctuation symbol
    X is lowered to a node Y if
    1. it is pairwise punctuation (two brackets, quotes, etc.)
    2. the left part L matching X is a direct daughter of Y
    3. X is the right neighbor of the rightmost terminal dominated by
       Y
    4. There is no punctuation between L and X
    """
    # collect all relevant terminals
    terms = trees.terminals(tree)
    parens = [(i, terminal) for (i, terminal)
              in enumerate(terms)
              if terminal.data['word'] in trees.C_PAIRPUNCT]
    done = []
    for (i, terminal) in parens:
        if terminal in done:
            continue
        # right neighbor of rightmost term of parent of punct
        p = terminal.parent
        pterms = trees.terminals(p)
        if pterms[-1] == terms[-1]:
            continue
        neighborpos = pterms[-1].data['num']
        neighbor = terms[neighborpos]
        if not neighbor.data['word'] in trees.C_PAIRPUNCT:
            continue
        punct_itm = False
        for x in range(i + 1, neighborpos):
            punct_itm = punct_itm or \
                        terms[x].data['word'] in trees.C_PAIRPUNCT
        if punct_itm:
            continue
        neighbor.parent.children.remove(neighbor)
        p.children.append(neighbor)
        neighbor.parent = p
        done.append(neighbor)
    return tree


def symetrify2(tree):
    """Reattach pairwise punctuation symetrically. A punctuation symbol
    X is lowered to a node Y if
    1. it is pairwise punctuation (two brackets, quotes, etc.)
    2. the left part L matching X is a direct daughter of Y
    3. X is the right neighbor of the rightmost terminal dominated by
       Y
    4. There is no punctuation between L and X
    """
    # collect all relevant terminals
    terms = trees.terminals(tree)
    parens = [(i, terminal) for (i, terminal)
              in enumerate(terms)
              if terminal.data['word'] in trees.C_PAIRPUNCT]
    done = []
    for (i, terminal) in parens:
        if terminal in done:
            continue
        # is left part? -------------------------
        # end of sentence? continue
        if terminal == terms[-1]:
            continue
        do_continue = False
        neighbor = trees.right_sibling(terminal)
        if not neighbor == None and len(trees.children(neighbor)) > 0:
            for neighborterm in trees.terminals(neighbor):
                if neighborterm.data['word'] in trees.C_PAIRPUNCT:
                    terminal.parent.children.remove(terminal)
                    neighbor.children.append(terminal)
                    terminal.parent = neighbor
                    done.append(neighborterm)
                    do_continue = True
                    break
            if do_continue:
                continue
        # is right part? ------------------------
        # parent of current punctuation
        p = terminal.parent
        pterms = trees.terminals(p)
        # parent dominates end of sentence? continue
        if pterms[-1] == terms[-1]:
            continue
        neighborpos = pterms[-1].data['num']
        # right neighbor of rightmost term of parent of punct
        neighbor = terms[neighborpos]
        # is not pairwise punct? continue
        if not neighbor.data['word'] in trees.C_PAIRPUNCT:
            continue
        # is there punctuation in the middle between the current
        # one and the above neighbor?
        punct_itm = False
        for x in range(i + 1, neighborpos):
            punct_itm = punct_itm or \
                        terms[x].data['word'] in trees.C_PAIRPUNCT
        # then continue
        if punct_itm:
            continue
        # otherwise move neighbor down
        neighbor.parent.children.remove(neighbor)
        p.children.append(neighbor)
        neighbor.parent = p
        # don't treat neighbor twice
        done.append(neighbor)
    return tree


def punct_verylow(tree):
    """Move all punctuation to the parent of its left terminal neighbor
    (when possible).

    Prerequisite: A previous application of root_attach().
    Parameters: none
    Output options: none
    """
    # collect all relevant terminals
    parens = [(i, terminal) for (i, terminal)
              in enumerate(trees.terminals(tree))
              if terminal.data['word'] in trees.C_PUNCT
              and i > 0]
    terminals = trees.terminals(tree)
    for (i, element) in parens:
        # exception: phrases which only have punctuation below them
        punct_only = True
        for child in element.parent.children:
            punct_only = punct_only and child.data['word'] in trees.C_PUNCT
        if not punct_only:
            target = terminals[i - 1].parent
            if not target == element.parent:
                element.parent.children.remove(element)
                element.parent = target
                target.children.append(element)
    return tree




def delete_punctuation(tree):
    """Remove punctuation terminals and write them out.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    terms = trees.terminals(tree)
    removal = []
    for i, terminal in enumerate(terms):
        if terminal.data['word'] in trees.C_PUNCT:
            removal.append(terminal)
    # skip tree if it's a punctuation-only tree
    if len(removal) == len(terms):
        sys.stderr.write('\ndelete_punctuation: no mod on %d, ' \
                         'punctuation only\n' % tree.data['sid'])
        return tree
    for terminal in removal:
        trees.delete_terminal(tree, terminal)
    return tree


def insert_terminals(tree, **params):
    """Insert terminal nodes in the tree, given in a parameter file
    in two colums, first column contains the string index, second the
    word. Inserted terminals will be attached to the root node.
    Example:

    A B D

    In order to insert a 'C' with POS tag 'X' between the 'B' and
    the 'D', you must specify

    2 C X

    No spaces in words allowed.

    Prerequisites: none
    Parameters: terminalfile:[file]
    Output options: none
    """
    terminals = defaultdict(int)
    with io.open(params['terminalfile']) as tf:
        for line in tf:
            line = line.strip()
            # throw away stuff after third space
            terminals[int(line[0])] = (line[1], line[2])
    for terminal_num in terminals:
        node = trees.Tree(trees.make_node_data())
        node.data['word'] = terminals[terminal_num][0]
        node.data['label'] = terminals[terminal_num][1]
        node.data['morph'] = trees.DEFAULT_MORPH
        node.data['lemma'] = trees.DEFAULT_LEMMA
        node.data['edge'] = trees.DEFAULT_EDGE
        node.data['num'] = terminal_num
        # shift other terminal numbers by one
        treeterms = trees.terminals(tree)
        for term in treeterms:
            if term.data['num'] >= terminal_num:
                term.data['num'] += 1
        # insert this one
        tree.children.append(node)
        node.parent = tree

