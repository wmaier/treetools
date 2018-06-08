"""
treetools: Tools for transforming treebank trees.

This module provides algorithms for tree transformations. Transformation
function take a single tree as argument and return the modified tree.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function, with_statement
import argparse
import sys
import io
import os
from collections import defaultdict
from . import trees, treeinput, treeoutput, misc, transformconst


def root_attach(tree, **params):
    """Reattach some children of the virtual root node in NeGra/TIGER/TueBa-DZ.
    In a nutshell, the algorithm moves all children of VROOT to the least
    common ancestor of the left neighbor terminal of the leftmost terminal and
    the right neighbor terminal of the rightmost terminal they dominate. We
    iterate through the children of VROOT left to right. Therefore, we might
    have to skip over adjacent children of VROOT on the right (which are not
    attached yet) in order to find the rightmost terminal. If the VROOT child
    constitutes the start or end of the sentence, or if the least common
    ancestor as described above is VROOT, it is not moved.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    tree_terms = trees.terminals(tree)
    # numbers of leftmost and rightmost terminal
    tree_min = tree_terms[0].data['num']
    tree_max = tree_terms[-1].data['num']
    # iterate through all VROOT children and try to attach them to the tree,
    # proceed left to right
    for child in trees.children(tree):
        # indices of terminal children of current child
        term_ind = [terminal.data['num'] for terminal in trees.terminals(child)]
        # left and right neighbor of lefmost and rightmost terminal child
        t_l = min(term_ind) - 1
        t_r = max(term_ind) + 1
        # on the right, we have to skip over all adjacent terminals which are
        # dominated by siblings of the current child of VROOT
        focus = child
        sibling = trees.right_sibling(focus)
        while not sibling == None:
            focus_ind = [terminal.data['num'] for terminal
                         in trees.terminals(focus)]
            sibling_ind = [terminal.data['num'] for terminal
                           in trees.terminals(sibling)]
            # skip over sibling if it starts left of the end
            # of the current focus node. Example: right sibling of current
            # child is a phrase, sibling of the phrase is punctuation
            # which interrupts this same phrase
            if min(sibling_ind) < max(focus_ind):
                sibling = trees.right_sibling(sibling)
                continue
            # gap found, i.e., sibling not adjacent to current node: we are done
            if min(sibling_ind) > max(focus_ind) + 1:
                break
            # neither skip nor done: update right boundary and try next sibling
            t_r = max(sibling_ind) + 1
            focus = sibling
            sibling = trees.right_sibling(sibling)
        # ignore if beyond sentence
        if t_l < tree_min or t_r > tree_max:
            continue
        # target for movement is least common ancestor of terminal neighbors
        target = trees.lca(tree_terms[t_l - 1], tree_terms[t_r - 1])
        # move/attach node
        child.parent.children.remove(child)
        target.children.append(child)
        child.parent = target
    return tree


def boyd_split(tree, **params):
    """For each continuous terminal block of a discontinuous node in tree,
    introduce a node which covers exactly this block. A single unique
    node is marked as head block if it covers the original head daugther
    of the unsplit node, to be determined recursively in case the head
    daugther has been split itself. For head finding a simple heuristic
    is used. The algorithm is documented in Boyd (2007) (ACL-LAW workshop).
    The algorithm relies on a previous application of head marking.

    Prerequisites: 
        A previous application of root_attach() and head marking.
    Parameters: none
    Output options:
        boyd_split_marking: leave asterisks on all block nodes
        boyd_split_numbering: marking + numbering of block nodes
    """
    h_block = 'head_block'
    # postorder since we have to 'continuify' lower trees first
    for subtree in trees.postorder(tree):
        # set default values
        subtree.data['split'] = False
        subtree.data[h_block] = True
        # split the children such that each sequence of children dominates
        # a continuous block of terminals
        blocks = []
        for child in trees.children(subtree):
            if len(blocks) == 0:
                blocks.append([])
            else:
                last_terminal = trees.terminals(blocks[-1][-1])[-1].data['num']
                if trees.terminals(child)[0].data['num'] > last_terminal + 1:
                    blocks.append([])
            blocks[-1].append(child)
        parent = subtree.parent
        # more than one block: do splitting.
        split = []
        if len(blocks) > 1:
            # unhook node
            parent.children.remove(subtree)
            subtree.parent = None
            # for each of the blocks, create a split node
            for i, block in enumerate(blocks):
                # the new node:
                split.append(trees.Tree(subtree.data))
                split[-1].data['split'] = True
                if not 'head' in split[-1].data:
                    raise ValueError("heads not marked?")
                split[-1].data['head'] = subtree.data['head']
                split[-1].data[h_block] = False
                split[-1].data['block_number'] = (i + 1)
                parent.children.append(split[-1])
                split[-1].parent = parent
                # iterate through children of original node in
                # the current block
                for child in block:
                    # mark current block as head block if the current child has
                    # the head attribute set (if the current child is a split
                    # node, it must also be marked as covering head block)
                    split[-1].data[h_block] = split[-1].data[h_block] \
                        or child.data['head'] and \
                        ((not child.data['split']) or child.data[h_block])
                    # move child below new block node
                    subtree.children.remove(child)
                    split[-1].children.append(child)
                    child.parent = split[-1]
    return tree


def raising(tree, **params):
    """Remove crossing branches by 'raising' nodes which cause crossing
    branches. This algorithm relies on a previous application of the Boyd
    splitting and removes all those newly introduced nodes which are *not*
    marked as head block (see above).

    Prerequisite: 
        Previous application of boyd_split().
    Parameters: none
    Output options: none
    """
    removal = []
    for subtree in trees.preorder(tree):
        if not subtree == tree:
            if subtree.data['split']:
                if not subtree.data['head_block']:
                    removal.append(subtree)
    for subtree in removal:
        parent = subtree.parent
        parent.children.remove(subtree)
        subtree.parent = None
        for child in trees.children(subtree):
            subtree.children.remove(child)
            parent.children.append(child)
            child.parent = parent
    return tree


def add_topnode(tree, **params):
    """Add a node with label TOP ensuring that there is a unary edge
    on top of the tree.

    Prerequisites: none
    Parameters: none
    Output options: none
    """
    top = trees.Tree(trees.make_node_data())
    top.data['label'] = u"TOP"
    top.children.append(tree)
    top.data['morph'] = trees.DEFAULT_MORPH
    top.data['edge'] = trees.DEFAULT_EDGE
    top.data['lemma'] = trees.DEFAULT_LEMMA
    top.data['sid'] = tree.data['sid']
    tree.parent = top
    return top


def substitute_terminals(tree, **params):
    """Substitute terminal nodes in the tree, given in a parameter file
    in four colums: sentence index, word index, word, part-of-speech. 
    The POS column is optional.

    Example: To substitute the 5th word in sentence 5 with "house"/NN,
    include

    5 5 house NN

    and omit NN if you only want to substitute the word an leave the
    POS tag as is.

    No spaces in words allowed, no double word indices per sentence
    allowed.

    Prerequisites: none
    Parameters: 
        quiet                : no messages
        terminalfile:[file]  : the terminals to insert
    Output options: none
    """
    # read terminals file only if filename is new
    if not hasattr(substitute_terminals, "fn") \
       or not substitute_terminals.fn == params['terminalfile']:
        substitute_terminals.fn = params['terminalfile']
        substitute_terminals.terminals = dict()
        with io.open(substitute_terminals.fn) as tf:
            for line in tf:
                line = line.strip().split()
                # probably no POS tag?
                if len(line) == 3:
                    line.append(None)
                if not int(line[0]) in substitute_terminals.terminals:
                    substitute_terminals.terminals[int(line[0])] = {}
                if not int(line[1]) in \
                   substitute_terminals.terminals[int(line[0])]:
                    substitute_terminals.terminals[int(line[0])][int(line[1])] \
                        = {}
                else:
                    del substitute_terminals.terminals
                    raise ValueError("in tree %d, double index %d" %
                                     (int(line[0]), int(line[1])))
                # throw away stuff after fourth space
                substitute_terminals.terminals[int(line[0])][int(line[1])] \
                    = (line[2], line[3])
    print(substitute_terminals.terminals)
    if not tree.data['sid'] in substitute_terminals.terminals:
        return tree
    terminals = trees.terminals(tree)
    for terminal_num in sorted(substitute_terminals.terminals[tree.data['sid']],
                               key=int):
        if not terminal_num in range(len(trees.terminals(tree)) + 1)[1:]:
            if not 'quiet' in params:
                print("sentence length %d, cannot insert at %d" \
                      % (len(trees.terminals(tree)),
                         terminal_num))
                continue
        terminal = terminals[terminal_num - 1]
        new_word = substitute_terminals.\
                   terminals[tree.data['sid']][terminal_num][0]
        terminal.data['word'] = new_word
        new_pos = substitute_terminals.\
                  terminals[tree.data['sid']][terminal_num][1]
        if not new_pos is None:
            terminal.data['label'] = new_pos
    return tree


def insert_terminals(tree, **params):
    """Insert terminal nodes in the tree, given in a parameter file
    in four colums: sentence index, word index, word, part-of-speech. 
    Inserted terminals will be attached to the root node.
    Example: Given a sentence with id [ID] and words

    A B D,

    in order to insert a 'C' with POS tag 'X' between the 'B' and
    the 'D', you must specify

    [ID] 2 C X

    No spaces in words allowed, no double word indices per sentence
    allowed.

    Prerequisites: none
    Parameters: 
        quiet                : no messages
        terminalfile:[file]  : the terminals to insert
    Output options: none
    """
    # read terminals file only if filename is new
    if not hasattr(insert_terminals, "fn") \
       or not insert_terminals.fn == params['terminalfile']:
        insert_terminals.fn = params['terminalfile']
        insert_terminals.terminals = dict()
        with io.open(insert_terminals.fn) as tf:
            for line in tf:
                line = line.strip().split()
                if not int(line[0]) in insert_terminals.terminals:
                    insert_terminals.terminals[int(line[0])] = {}
                if not int(line[1]) in insert_terminals.terminals[int(line[0])]:
                    insert_terminals.terminals[int(line[0])][int(line[1])] = {}
                else:
                    del insert_terminals.terminals
                    raise ValueError("in tree %d, double index %d" %
                                     (int(line[0]), int(line[1])))
                # throw away stuff after fourth space
                insert_terminals.terminals[int(line[0])][int(line[1])] \
                    = (line[2], line[3])
    if not tree.data['sid'] in insert_terminals.terminals:
        return tree
    for terminal_num in sorted(insert_terminals.terminals[tree.data['sid']],
                               key=int):
        if terminal_num > len(trees.terminals(tree)) + 1 \
                or terminal_num == 0:
            if 'quiet' not in params:
                print("sentence length %d, cannot insert at %d"
                      % (len(trees.terminals(tree)),
                         terminal_num))
            continue
        node = trees.Tree(trees.make_node_data())
        node.data['word'] = insert_terminals. \
            terminals[tree.data['sid']][terminal_num][0]
        node.data['label'] = insert_terminals. \
            terminals[tree.data['sid']][terminal_num][1]
        node.data['morph'] = trees.DEFAULT_MORPH
        node.data['lemma'] = trees.DEFAULT_LEMMA
        node.data['edge'] = trees.DEFAULT_EDGE
        node.data['num'] = terminal_num
        # shift other terminal numbers by one
        # print("inserting in %d at %d" % (tree.data['sid'], terminal_num))
        treeterms = trees.terminals(tree)
        for term in treeterms:
            if term.data['num'] >= terminal_num:
                term.data['num'] += 1
        # insert this one
        tree.children.append(node)
        node.parent = tree
    return tree


def punctuation_delete(tree, **params):
    """Remove punctuation terminals and write them out
    on stdout.

    Prerequisite: none
    Parameters: 
        quiet : no messages
    Output options: none
    """
    removal = [term for term in trees.terminals(tree)
               if term.data['word'] in trees.PUNCT]
    output = ["%s\t%s\t%s\t%s" % (tree.data['sid'],
                                  terminal.data['num'],
                                  terminal.data['word'],
                                  terminal.data['label'])
              for terminal in removal]
    # skip tree if it's a punctuation-only tree
    if len(removal) == len(trees.terminals(tree)):
        if not 'quiet' in params:
            sys.stderr.write('\ndelete_punctuation: no mod on %d, ' \
                                 'punctuation only\n' % tree.data['sid'])
    else:
        for terminal in removal:
            tree = trees.delete_terminal(tree, terminal)
        for line in output:
            print(line)
    return tree


def punctuation_verylow(tree, **params):
    """Move all punctuation to the parent of its left terminal neighbor
    (when possible).

    Prerequisite: 
        A previous application of root_attach().
    Parameters: none
    Output options: none
    """
    # collect all relevant terminals
    parens = [(i, terminal) for (i, terminal)
              in enumerate(trees.terminals(tree))
              if terminal.data['word'] in trees.PUNCT
              and i > 0]
    terminals = trees.terminals(tree)
    for (i, element) in parens:
        # exception: phrases which only have punctuation below them
        if not all([child.data['word'] in trees.PUNCT \
                    for child in element.parent.children]):
            target = terminals[i - 1].parent
            if not target == element.parent:
                element.parent.children.remove(element)
                element.parent = target
                target.children.append(element)
    return tree


def punctuation_symetrify(tree, **params):
    """Reattach pairwise punctuation symetrically. Loop through all
    punctuation terminals t that can occur in pairs from left to right.
    First check if t is on the left corner of a phrase which dominates
    a terminal that is a potential right part for t. If not applicable,
    check if t is on the right corner of a phrase and has a potential
    left part as a terminal child of this phrase.

    Prerequisite: 
        A previous application of root_attach
    Parameters: 
        relc [LABEL] : include commas before words POS tagged
                       LABEL (relative clauses)
    Output options: none
    """
    # collect all relevant terminals
    terms = trees.terminals(tree)
    parens = [(i, terminal) for (i, terminal) in enumerate(terms)
              if terminal.data['word'] in trees.PAIRPUNCT]
    relpron = None
    if 'relc' in params:
        relpron = params['relc']
        parens = [(i, terminal) for (i, terminal) in enumerate(terms)
                  if terminal.data['word'] in trees.PAIRPUNCT
                  or (i < len(terms) - 1 
                      and terms[i + 1].data['label'] == relpron)]
    done = []
    for (i, terminal) in parens:
        # don't treat stuff twice
        if terminal in done:
            continue
        leftmost_term = trees.terminals(terminal.parent)[0]
        if not leftmost_term == terms[0]:
            candnum = leftmost_term.data['num'] - 1
            cand = terms[candnum - 1]
            if cand.data['word'] in trees.PAIRPUNCT \
               and not cand in done:
                cand.parent.children.remove(cand)
                cand.parent = terminal.parent
                terminal.parent.children.append(cand)
                done.append(cand)
                done.append(terminal)
        if terminal in done:
            continue
        rightmost_term = trees.terminals(terminal.parent)[-1]
        if not rightmost_term == terms[-1]:
            candnum = rightmost_term.data['num'] + 1
            cand = terms[candnum - 1]
            if cand.data['word'] in trees.PAIRPUNCT \
               and not cand in done:
                cand.parent.children.remove(cand)
                cand.parent = terminal.parent
                terminal.parent.children.append(cand)
                done.append(cand)
                done.append(terminal)
    return tree


def punctuation_root(tree, **params):
    """Attach all punctuation to the root node.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    terms = trees.terminals(tree)
    punct = [terminal for terminal in terms
             if terminal.data['word'] in trees.PUNCT \
             and len(trees.children(terminal.parent)) > 1]
    for p in punct:
        p.parent.children.remove(p)
        tree.children.append(p)
        p.parent = tree
    return tree


def ptb_delete_traces(tree, **params):
    """Delete PTB traces and all co-indexation.
    Labels will swap positions with terminals, i.e., -NONE- will be
    terminal and trace symbol label. Gap indices ('=') are deleted.

    Prerequisite: none
    Parameters:
        keep [LABELS] : Trace labels which are to be kept,
                        comma-separated. Co-indexation will
                        be deleted nevertheless.
        keepall       : Keep all trace labels. Co-indexation will
                        be deleted nevertheless.
        keepcoindex   : For all labels which are to be kept,
                        keep the co-indexation, too.
        slash [LABELS]: Perform slash feature annotation on
                        path from trace to antecedent. Annotation
                        will be the label of the filler up to the
                        first dash. Annotation only performed
                        for given labels if labels are given,
                        otherwise for all labels
    Output options: none
    """
    keep = []
    if 'keep' in params:
        keep = params['keep'].split(',')
    keepcoindex = 'keepcoindex' in params
    keepall = 'keepall' in params
    slash = []
    do_slash = False
    if 'slash' in params:
        do_slash = True
        if not type(params['slash']) is bool:
            slash = params['slash'].split(',')
    traces = [terminal for terminal in trees.terminals(tree)
                  if terminal.data['label'] == "-NONE-"]
    index_to_traces = defaultdict(list)
    index_to_nonterms = defaultdict(list)
    # map indices to trace nodes and deleted indices from labales
    for trace in traces:
        tracelabel = trees.parse_label(trace.data['word'])
        coindex = str(tracelabel.coindex)
        if not keepcoindex:
            tracelabel.coindex = ""
        tracelabel.gapindex = ""
        tracelabel = trees.format_label(tracelabel)
        if keepall or tracelabel in keep:
            if len(coindex) > 0:
                index_to_traces[coindex].append(trace)
            trace.data['label'] = tracelabel
            trace.data['word'] = "-NONE-"
        else:
            trees.delete_terminal(tree, trace)
    # map indices to non-terminals (except preterminals)
    for node in trees.preorder(tree):
        if len(trees.children(node)) == 0:
            continue
        label = trees.parse_label(node.data['label'])
        if len(label.coindex) > 0:
            index_to_nonterms[label.coindex].append(node)
        # already delete indices
        label.gapindex = ""
        if not keepcoindex:
            label.coindex = ""
        node.data['label'] = trees.format_label(label)
    # do slash annotatoin
    if do_slash:
        # check if one index maps to several nonterms aka uniqueness of fillers
        if (any([len(index_to_nonterms[index]) > 1 for index in index_to_nonterms])):
            # if necessary compute new mapping
            print("\n", file=sys.stderr)
            print(' '.join([x.data['word'] for x in trees.terminals(tree)]), \
                  file=sys.stderr)
            print("fillers not unique: resolving traces bottom-up", \
                  file=sys.stderr)
            trace_filler = {}
            new_index = 1
            for index in index_to_traces:
                fillers = index_to_nonterms[index]
                for trace in index_to_traces[index]:
                    mapping_found = False
                    cursor = trace
                    while not cursor.parent is None:
                        for filler in fillers:
                            if cursor.parent is filler:
                                # dominance
                                trace_filler[trace] = (new_index, filler)
                                new_index += 1
                                mapping_found = True
                            else:
                                # c-command
                                for child in trees.children(cursor.parent):
                                    for filler in fillers:
                                        if child is filler:
                                            trace_filler[trace] = (new_index,
                                                                   child)
                                            new_index += 1
                                            mapping_found = True
                                            break
                                    # MUCH BETTER THAN GOTO!
                                    if mapping_found:
                                        break
                            # MUCH BETTER THAN GOTO!
                            if mapping_found:
                                break
                        # MUCH BETTER THAN GOTO!
                        if mapping_found:
                            break
                        cursor = cursor.parent
                    if cursor.parent == None and not mapping_found:
                        raise ValueError("no mapping found")
            newindex = 1
            new_index_to_traces = defaultdict(list)
            new_index_to_nonterms = defaultdict(list)
            for trace in trace_filler:
                index, filler = trace_filler[trace]
                new_index_to_traces[str(index)].append(trace)
                new_index_to_nonterms[str(index)].append(filler)
            index_to_traces = new_index_to_traces
            index_to_nonterms = new_index_to_nonterms
        # check if there is no filler for some trace, fillers with index and no 
        # trace are no problem!
        if (any([index not in index_to_nonterms for index in index_to_traces])):
            print("\n", file=sys.stderr)
            print(' '.join([x.data['word'] \
                            for x in trees.terminals(tree)]), \
                  file=sys.stderr)
            print("no filler for trace, deleting it", \
                  file=sys.stderr)
            to_delete = []
            for index in index_to_traces:
                if not index in index_to_nonterms:
                    to_delete.append(index)
            for index in to_delete:
                for trace in index_to_traces[index]:
                    trees.delete_terminal(tree, trace)
                del index_to_traces[index]
        # resolve traces and annotate stuff
        for coindex in index_to_traces:
            for trace in index_to_traces[coindex]:
                if len(slash) > 0:
                    if not trees.parse_label(trace.data['label']).label in slash:
                        continue
                # always has length 1 (see above)
                filler = index_to_nonterms[coindex][0]
                goal = trees.lca(filler, trace)
                if goal == None:
                    if filler in trees.dominance(trace):
                        goal = filler
                    else:
                        raise ValueError("filler neither c-commands nor dominates")
                # annotate path from filler to goal
                annot = trees.parse_label(filler.data['label']).label
                cursor = filler
                while not cursor == goal:
                    if not cursor == filler:
                        cursor.data['label'] += "/" + annot
                    cursor = cursor.parent
                cursor = trace
                while not cursor == goal:
                    if not cursor == trace:
                        cursor.data['label'] += "/" + annot
                    cursor = cursor.parent
    return tree


def negra_mark_heads(tree, **params):
    """Mark the head child of each node in a NeGra/TIGER tree using a simple
    heuristic. If there is child with a HD edge, it will be marked. Otherwise,
    the rightmost child with a NK edge will be marked. If there is no such
    child, the leftmost child will be marked.

    Prerequisite: none
    Parameters: none
    Output options:
        mark_heads_marking: Mark heads with an '
    """
    tree.data['head'] = False
    for subtree in trees.preorder(tree):
        if trees.has_children(subtree):
            subtree_children = trees.children(subtree)
            edges = [child.data['edge'] for child in subtree_children]
            # default leftmost
            index = 0
            # if applicable leftmost HD
            if 'HD' in edges:
                index = edges.index('HD')
            # otherwise if applicable rightmost NK
            elif 'NK' in edges:
                index = (len(edges) - 1) - edges[::-1].index('NK')
            subtree_children[index].data['head'] = True
            for i, child in enumerate(subtree_children):
                if not i == index:
                    child.data['head'] = False
    return tree


def mark_heads_by_rules(tree, **params):
    """Mark the head child of each node in a tree using Collins-style head
    rules. Rule file must be specified as parameter mark_heads_rulefile, 
    or 'standard' rules for NeGra/TIGER ('negra') or the Penn Treebank ('ptb')
    can be loaded with the parameter mark_heads_preset.

    Prerequisite: none
    Parameters:
        mark_heads_rulefile: Path to rulefile
        mark_heads_preset: Instead of rulefile, can be 'negra' or 'ptb'
    Output options: none
    """
    rules = []
    if 'mark_heads_preset' in params and 'mark_heads_rulefile' in params:
        raise ValueError("specify either head rule preset or rule file")
    if 'mark_heads_preset' in params:
        if params['mark_heads_preset'] == 'negra':
            rules = transformconst.HEAD_RULES_PTB
        elif params['mark_heads_preset'] == 'ptb':
            rules = transformconst.HEAD_RULES_NEGRA
        else:
            raise ValueError("unknown head rule preset "
                             + str(params['mark_heads_preset']))
    elif 'mark_heads_rulefile' in params:
        if not len(params['mark_heads_rulefile']) == 0:
            raise ValueError("not yet implemented")
    else:
        raise ValueError("must specify head rule preset or rule file")
    tree.data['head'] = False
    for subtree in trees.preorder(tree):
        parent_label = trees.parse_label(subtree.data['label']).label
        children = trees.children(subtree)
        children_label = [trees.parse_label(child.data['label']).label
                          for child in children]
        if len(children) > 0:
            headpos = transformconst.get_headpos_by_rule(parent_label,
                                                         children_label, rules)
            for i, child in enumerate(children):
                children[i].data['head'] = i == headpos
    return tree


def _binarize_tree(tree, bare_bin_labels):
    """Recursively binarize this tree.
    """
    if not trees.has_children(tree):
        return tree
    for child in trees.children(tree):
        _binarize_tree(child, bare_bin_labels)
    if len(trees.children(tree)) > 2:
        direction = "left"
        remaining = trees.children(tree)
        last_tree = tree
        tree.children = []
        label = tree.data['label']
        child = None
        binarization_tree = None
        while len(remaining) > 2:
            if 'head' not in remaining[0].data:
                raise ValueError("heads not marked?")
            if remaining[0].data['head']:
                direction = 'right'
            binarization_tree = trees.Tree(trees.make_node_data_fill())
            label_no_coindex = trees.parse_label(label)
            label_no_coindex.coindex = ""
            label_no_coindex = trees.format_label(label_no_coindex)
            binarization_tree.data['label'] = '@'
            if not bare_bin_labels:
                binarization_tree.data['label'] += label_no_coindex
            binarization_tree.data['head'] = True
            if direction == 'left':
                child = remaining[0]
                remaining = remaining[1:]
            elif direction == 'right':
                child = remaining[-1]
                remaining = remaining[:-1]
            last_tree.children.append(binarization_tree)
            last_tree.children.append(child)
            binarization_tree.parent = last_tree
            child.parent = last_tree
            last_tree = binarization_tree
        for i in range(2):
            child = remaining[i]
            binarization_tree.children.append(child)
            child.parent = binarization_tree


def binarize(tree, **params):
    """Destructively binarize the tree.

    Prerequisite: none
    Parameters:
        bare_bin_labels       : only use '@' as binarization label
    Output options: none
    """
    bare_bin_labels = 'bare_bin_labels' in params
    _binarize_tree(tree, bare_bin_labels)
    return tree


def _collapse_unary_chains(tree):
    """Recursively collapse unary chains.
    """
    while len(trees.children(tree)) == 1:
        tree.data['label'] += "+" + trees.children(tree)[0].data['label']
        grandchildren = trees.children(trees.children(tree)[0])
        if len(grandchildren) == 0:
            # it is a terminal and we have to keep its data
            tree.data['num'] = trees.children(tree)[0].data['num']
            tree.data['word'] = trees.children(tree)[0].data['word']
            tree.data['lemma'] = trees.children(tree)[0].data['lemma']
        tree.children = []
        for grandchild in grandchildren:
            tree.children.append(grandchild)
            grandchild.parent = tree
    for child in trees.children(tree):
        _collapse_unary_chains(child)


def collapse_unary_chains(tree, **params):
    """Collapse unary chains and concatenate all labels.
    May not make sense for sentences of length one.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    _collapse_unary_chains(tree)
    return tree


def _uncollapse_unary_chains(tree):
    """Recursively uncollapse unary chains.
    """
    unary = tree
    while tree.data['label'].find("+") > -1:
        # tree.parent -> tree -> c1 .. cn
        # tree.parent -> unary -> tree -> c1 .. cn
        ind = tree.data['label'].find("+")
        unary = trees.Tree(tree.data)
        unary.data['label'] = tree.data['label'][:ind]
        tree.data['label'] = tree.data['label'][ind + 1:]
        if not tree.parent is None:
            tree.parent.children.remove(tree)
            tree.parent.children.append(unary)
        unary.children.append(tree)
        unary.parent = tree.parent
        tree.parent = unary
    for child in trees.children(tree):
        _uncollapse_unary_chains(child)
    return unary


def uncollapse_unary_chains(tree, **params):
    """Un-collapse unary chains collapsed earlier by
    collapse_unary_chains.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    tree = _uncollapse_unary_chains(tree)
    return tree


def filter_by_length(tree, **params):
    """Return None for all trees with a number of terminals
    less than, greater than, or equal to the given filtervalue.

    Prerequisite: none
    Parameters:
        filteroperator      : one of lt, gt, eq
        filtervalue         : number of terminals
    Output options: none
    """
    length = len(trees.terminals(tree))
    oper = params['filteroperator']
    val = params['filtervalue']
    if oper == 'lt':
        if length < val:
            return None
    elif oper == 'gt':
        if length > val:
            return None
    elif oper == 'eq':
        if length == val:
            return None
    return tree


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('transform',
                                   usage='%(prog)s src dest [options]',
                                   formatter_class=argparse.
                                   RawDescriptionHelpFormatter,
                                   description='Offers transformation and '
                                   'format conversion for constituency '
                                   'treebank trees.')
    parser.add_argument('src', help='input file')
    parser.add_argument('dest', help='output file')
    parser.add_argument('--counting', metavar='n', type=int,
                        help='display number of processed sentences every n '
                        ' sentences (default: %(default)s)',
                        default=100)
    parser.add_argument('--trans', nargs='+', metavar='T',
                        help='transformations to apply (default: %(default)s)',
                        default=[])
    parser.add_argument('--params', nargs='+', metavar='P',
                        help='space separated list of transformation '
                        'parameters P of the form (default: '
                        '%(default)s)',
                        default=[])
    parser.add_argument('--src-format', metavar='FMT',
                        choices=[fun.__name__
                                 for fun in treeinput.INPUT_FORMATS],
                        help='input format (default: %(default)s)',
                        default='export')
    parser.add_argument('--src-enc', metavar='ENCODING',
                        help='input encoding (default: %(default)s)',
                        default='utf-8')
    parser.add_argument('--src-opts', nargs='+', metavar='O',
                        help='space separated list of options O for reading '
                        'input of the form key:value '
                        '(default: %(default)s)',
                        default=[])
    parser.add_argument('--dest-format', metavar='FMT',
                        choices=[fun.__name__
                                 for fun in treeoutput.OUTPUT_FORMATS],
                        help='output format (default: %(default)s)',
                        default='export')
    parser.add_argument('--dest-enc', metavar='ENCODING',
                        help='output encoding (default: %(default)s)',
                        default='utf-8')
    parser.add_argument('--dest-opts', nargs='+', metavar='O',
                        help='space separated list of options O for writing '
                        'output of the form key:value '
                        '(default: %(default)s)',
                        default=[])
    parser.add_argument('--split', metavar='HOW',
                        help='split output in several parts ' \
                            'according to a split specification. Syntax: ' \
                            '"P1_.._Pn" where each Pi is a part ' \
                            'specification, which is either the keyword ' \
                            '"rest" or a number suffixed by either "#" ' \
                            '(specifying an absolute number of sentences) ' \
                            'or "%%" (specifiying a percentage of all ' \
                            'sentences) (default: no splitting).',
                        default='')
    parser.add_argument('--usage', nargs=0, help='show detailed information ' \
                        'about available algorithms, input options and ' \
                        'output options.', action=UsageAction)
    parser.set_defaults(func=run)
    return parser


class UsageAction(argparse.Action):
    """Custom action which shows extended help on available transformation
    options.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        title_str = misc.bold("%s help" % sys.argv[0])
        help_str = "\n\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n" \
                   % (misc.bold("%s\n%s" %
                                ('available transformations: ',
                                 '========================== ')),
                      misc.get_doc(TRANSFORMATIONS),
                      misc.bold("%s\n%s" %
                                ('available input formats: ',
                                 '======================== ')),
                      misc.get_doc(treeinput.INPUT_FORMATS),
                      misc.bold("%s\n%s" %
                                ('available input options: ',
                                 '======================== ')),
                      misc.get_doc_opts(treeinput.INPUT_OPTIONS),
                      misc.bold("%s\n%s" %
                                ('available output formats: ',
                                 '========================= ')),
                      misc.get_doc(treeoutput.OUTPUT_FORMATS),
                      misc.bold("%s\n%s" %
                                ('available output options: ',
                                 '========================= ')),
                      misc.get_doc_opts(treeoutput.OUTPUT_OPTIONS))
        print("\n%s%s" % (title_str, help_str))
        sys.exit()


def run(args):
    """Runs the transformation given command line arguments.
    """
    sys.stderr.write("reading from '%s' in format '%s' and encoding '%s'\n"
                     % (args.src, args.src_format, args.src_enc))
    sys.stderr.write("writing to '%s' in format '%s' and encoding '%s'\n"
                     % (args.dest, args.dest_format, args.dest_enc))
    sys.stderr.write("applying %s\n" % args.trans)
    if not args.split == "":
        sys.stderr.write("splitting output like this: %s\n" % args.split)
    cnt = 1
    params = misc.options_dict(args.params)
    if args.split == '':
        files = []
        if os.path.isdir(args.src):
            for srcfile in os.listdir(args.src):
                srcfile = os.path.join(args.src, srcfile)
                destfile = "%s.dest" % srcfile
                files.append((srcfile, destfile))
        else:
            files.append((args.src, args.dest))
        for src, dest in files:
            print("%s --> %s" % (src, dest), file=sys.stderr)
            with io.open(dest, 'w', encoding=args.dest_enc) as dest_stream:
                getattr(treeoutput, args.dest_format + '_begin')\
                    (dest_stream,
                     **misc.options_dict(args.dest_opts))
                for tree in getattr(treeinput,
                                    args.src_format)(src, args.src_enc,
                                                     **misc.options_dict \
                                                     (args.src_opts)):
                    for algorithm in args.trans:
                        tree = globals()[algorithm](tree, **params)
                        if tree is None:
                            break
                    if tree is not None:
                        getattr(treeoutput, args.dest_format)(tree, dest_stream,
                                                              **misc.options_dict
                                                              (args.dest_opts))
                    if cnt % args.counting == 0:
                        sys.stderr.write("\r%d" % cnt)
                    cnt += 1
                getattr(treeoutput, args.dest_format + '_end')\
                    (dest_stream,
                     **misc.options_dict(args.dest_opts))
            sys.stderr.write("\n")
    else:
        if os.path.isdir(args.src):
            raise ValueError("cannot split input when reading entire directory")
        cnt = 1
        tree_list = []
        sys.stderr.write("reading...\n")
        for tree in getattr(treeinput, args.src_format)(args.src, args.src_enc,
                                                        **misc.options_dict \
                                                        (args.src_opts)):
            for algorithm in args.trans:
                tree = globals()[algorithm](tree,
                                            **misc.options_dict(args.params))
                if tree is None:
                    break
            if tree is not None:
                tree_list.append(tree)
            if cnt % args.counting == 0:
                sys.stderr.write("\r%d" % cnt)
            cnt += 1
        sys.stderr.write("\n")
        parts = treeoutput.parse_split_specification(args.split, len(tree_list))
        tree_iter = iter(tree_list)
        sys.stderr.write("writing parts of sizes %s\n" % str(parts))
        for i, part_size in enumerate(parts):
            sys.stderr.write("writing part %d\n" % i)
            with io.open("%s.%d" % (args.dest, i), 'w',
                         encoding=args.dest_enc) as dest_stream:
                for tree_ind in range(0, part_size):
                    getattr(treeoutput, args.dest_format) \
                        (next(tree_iter), dest_stream, \
                         **misc.options_dict(args.dest_opts))
                    if tree_ind % args.counting == 0:
                        sys.stderr.write("\r%d" % tree_ind)
                sys.stderr.write("\n")


TRANSFORMATIONS = [root_attach, boyd_split, raising, add_topnode,
                   substitute_terminals, insert_terminals,
                   punctuation_delete, punctuation_verylow,
                   punctuation_symetrify, punctuation_root,
                   negra_mark_heads, mark_heads_by_rules,
                   ptb_delete_traces, binarize, collapse_unary_chains,
                   filter_by_length]
