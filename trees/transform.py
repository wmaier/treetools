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
from . import trees, treeinput, treeoutput, misc


def root_attach(tree):
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
    """ 
    tree_terms = trees.terminals(tree)
    # numbers of leftmost and rightmost terminal
    tree_min = tree_terms[0]['num']
    tree_max = tree_terms[-1]['num']
    # iterate through all VROOT children and try to attach them to the tree,
    # proceed left to right
    for child in trees.children(tree):
        # indices of terminal children of current child
        term_ind = [terminal['num'] for terminal in trees.terminals(child)]
        # left and right neighbor of lefmost and rightmost terminal child
        t_l = min(term_ind) - 1
        t_r = max(term_ind) + 1
        # on the right, we have to skip over all adjacent terminals which are 
        # dominated by siblings of the current child of VROOT
        focus = child
        sibling = trees.right_sibling(focus)
        while not sibling == None:
            focus_ind = [terminal['num'] for terminal 
                         in trees.terminals(focus)]
            sibling_ind = [terminal['num'] for terminal 
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
        child['parent']['children'].remove(child)
        target['children'].append(child)
        child['parent'] = target
    return tree


def mark_heads(tree):
    """Mark the head child of each node in a NeGra/TIGER tree using a simple 
    heuristic. If there is child with a HD edge, it will be marked. Otherwise,
    the rightmost child with a NK edge will be marked. If there is no such
    child, the leftmost child will be marked.
    Prerequisite: none
    Output options:
        mark_heads_marking: Mark heads with an '
    """
    tree['head'] = False
    for subtree in trees.preorder(tree):
        if trees.has_children(subtree):
            subtree_children = trees.children(subtree)
            edges = [child['edge'] for child in subtree_children]
            # default leftmost
            index = 0
            # if applicable leftmost HD
            if 'HD' in edges:
                index = edges.index('HD')
            # otherwise if applicable rightmost NK
            elif 'NK' in edges:
                index = (len(edges) - 1) - edges[::-1].index('NK') 
            subtree_children[index]['head'] = True
            for i, child in enumerate(subtree_children):
                if not i == index:
                    child['head'] = False
    return tree


def boyd_split(tree):
    """For each continuous terminal block of a discontinuous node in tree, 
    introduce a node which covers exactly this block. A single unique
    node is marked as head block if it covers the original head daugther
    of the unsplit node, to be determined recursively in case the head
    daugther has been split itself. For head finding a simple heuristic 
    is used. The algorithm is documented in Boyd (2007) (ACL-LAW workshop).
    The algorithm relies on a previous application of head marking.
    Prerequisites: A previous application of root_attach() and head marking.
    Output options: 
        boyd_split_marking: leave asterisks on all block nodes
        boyd_split_numbering: marking + numbering of block nodes
    """
    # postorder since we have to 'continuify' lower trees first
    for subtree in trees.postorder(tree):
        # set default values
        subtree['split'] = False
        subtree['head_block'] = True
        # split the children such that each sequence of children dominates
        # a continuous block of terminals
        blocks = []
        for child in trees.children(subtree):
            if len(blocks) == 0:
                blocks.append([])
            else:
                last_terminal = trees.terminals(blocks[-1][-1])[-1]['num']
                if trees.terminals(child)[0]['num'] > last_terminal + 1:
                    blocks.append([])
            blocks[-1].append(child)
        parent = subtree['parent']
        # more than one block: do splitting.
        split = []
        if len(blocks) > 1:
            # unhook node
            parent['children'].remove(subtree)
            subtree['parent'] = None
            # for each of the blocks, create a split node
            for i, block in enumerate(blocks):
                # the new node:
                split.append(trees.make_tree(subtree))
                split[-1]['split'] = True
                split[-1]['head'] = subtree['head']
                split[-1]['head_block'] = False
                split[-1]['block_number'] = (i + 1)
                parent['children'].append(split[-1])
                split[-1]['parent'] = parent
                # iterate through children of original node in
                # the current block
                for child in block:
                    # mark current block as head block if the current child has
                    # the head attribute set (if the current child is a split 
                    # node, it must also be marked as covering head block)
                    split[-1]['head_block'] = split[-1]['head_block'] \
                        or child['head'] and \
                        ((not child['split']) or child['head_block'])
                    # move child below new block node
                    subtree['children'].remove(child)
                    split[-1]['children'].append(child)
                    child['parent'] = split[-1]
    return tree


def raising(tree):
    """Remove crossing branches by 'raising' nodes which cause crossing
    branches. This algorithm relies on a previous application of the Boyd
    splitting and removes all those newly introduced nodes which are *not*
    marked as head block (see above). 
    Prerequisite: Previous application of boyd_split().
    """
    removal = []
    for subtree in trees.preorder(tree):
        if not subtree == tree:
            if subtree['split']:
                if not subtree['head_block']:
                    removal.append(subtree)
    for subtree in removal:
        parent = subtree['parent']
        parent['children'].remove(subtree)
        subtree['parent'] = None
        for child in trees.children(subtree):
            subtree['children'].remove(child)
            parent['children'].append(child)
            child['parent'] = parent
    return tree


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('transform', 
                                   usage='%(prog)s src dest [options]', 
                                   formatter_class=argparse.
                                   RawDescriptionHelpFormatter,
                                   description='Offers transformation and ' \
                                       'format conversion for constituency ' \
                                       'treebank trees.')
    parser.add_argument('src', help='input file')
    parser.add_argument('dest', help='output file')
    parser.add_argument('--trans', nargs='+', metavar='T', 
                        help='transformations to apply (default: %(default)s)', 
                        default=[])
    parser.add_argument('--params', nargs='+', metavar='P', 
                        help='space separated list of transformation ' \
                            'parameters P of the form (default: ' \
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
                        help='space separated list of options O for reading ' \
                            'input of the form key:value ' \
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
                        help='space separated list of options O for writing ' \
                            'output of the form key:value ' \
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
                            'sentences) (default: no splitting).' , 
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
                   % (misc.bold('available transformations: '),
                      misc.get_doc(TRANSFORMATIONS),
                      misc.bold('available input formats: '),
                      misc.get_doc(treeinput.INPUT_FORMATS),
                      misc.bold('available input options: '),
                      misc.get_doc_opts(treeinput.INPUT_OPTIONS),
                      misc.bold('available output formats: '),
                      misc.get_doc(treeoutput.OUTPUT_FORMATS),
                      misc.bold('available output options: '),
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
    if args.split == '':
        with io.open(args.dest, 'w', encoding=args.dest_enc) as dest_stream:
            for tree in getattr(treeinput, 
                                args.src_format)(args.src, args.src_enc, 
                                                 **misc.options_dict \
                                                 (args.src_opts)):
                for algorithm in args.trans:
                    tree = globals()[algorithm](tree, 
                                                **misc.options_dict \
                                                (args.params))
                getattr(treeoutput, args.dest_format)(tree, dest_stream, 
                                                      **misc.options_dict \
                                                      (args.dest_opts))
                if cnt % 100 == 0:
                    sys.stderr.write("\r%d" % cnt)
                cnt += 1
        sys.stderr.write("\n")
    else:
        cnt = 1
        tree_list = []
        sys.stderr.write("reading...\n")
        for tree in getattr(treeinput, args.src_format)(args.src, args.src_enc,
                                                        **misc.options_dict \
                                                        (args.src_opts)):
            for algorithm in args.trans:
                tree = globals()[algorithm](tree, 
                                            **misc.options_dict \
                                            (args.params))
            tree_list.append(tree)
            if cnt % 100 == 0:
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
                        (tree_iter.next(), dest_stream, \
                         **misc.options_dict(args.dest_opts))
                    if tree_ind % 100 == 0: 
                        sys.stderr.write("\r%d" % tree_ind)
                sys.stderr.write("\n")

TRANSFORMATIONS = [root_attach, mark_heads, boyd_split, raising]

