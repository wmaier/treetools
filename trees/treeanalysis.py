"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for analyzing trees.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import division, print_function
import argparse
import sys
from collections import Counter
from . import trees, treeinput, misc


class PosTags(object):
    """Accumulates statistics concerning POS tags over several trees.
    """
    def __init__(self):
        self.tags = []

    def run(self, tree):
        """Collect and count POS tags (preterminal labels) in a single tree.
        """
        for term in trees.terminals(tree):
            self.tags.append(term.data['label'])

    def done(self):
        """Print summary and write tags. To be extended.
        """
        tags_cnt = Counter(self.tags)
        print("*** POS tag summary ***")
        print()
        print("%d different tags" % len(tags_cnt))
#        print("Per tag: ")
#        for tag in tags_cnt:
#            print("%s %d" % (tag, tags_cnt[tag]))


class SentenceCount(object):
    """Counts sentences.
    """
    def __init__(self):
        self.cnt = 0

    def run(self, tree):
        """Collect and count POS tags (preterminal labels) in a single tree.
        """
        self.cnt += 1

    def done(self):
        """Print summary and write tags. To be extended.
        """
        print("*** Sentence count summary ***")
        print()
        print("%d sentences" % self.cnt)


def gap_degree_node(node):
    """Compute gap degree for a single node.
    """
    if not trees.has_children(node):
        return 0
    node_gap_deg = 0
    terms = trees.terminals(node)
    for i, _ in enumerate(terms[:-1]):
        if terms[i].data['num'] + 1 < terms[i + 1].data['num']:
            node_gap_deg += 1
    return node_gap_deg


class GapDegree(object):
    """Accumulates statistics concerning gap degree over several trees.
    """
    def __init__(self):
        # counts gap degree for each node
        self.gaps_per_node = {}
        # counts highest node gap degree for each tree
        self.gaps_per_tree = {}

    def run(self, tree):
        """Return the maximal gap degree of any node of the given tree.
        """
        tree_gap_deg = 0
        for subtree in trees.preorder(tree):
            # skip terminals
            if trees.has_children(subtree):
                node_gap_deg = gap_degree_node(subtree)
                # store node gap degree
                if not node_gap_deg in self.gaps_per_node:
                    self.gaps_per_node[node_gap_deg] = 0
                self.gaps_per_node[node_gap_deg] += 1
                tree_gap_deg = max(tree_gap_deg, node_gap_deg)
        # store tree gap degree
        if not tree_gap_deg in self.gaps_per_tree:
            self.gaps_per_tree[tree_gap_deg] = 0
        self.gaps_per_tree[tree_gap_deg] += 1

    def done(self):
        """Compute and print summary about gap degree statistics collected
        during all runs of run().
        """
        # compute stuff
        # how many trees and nodes in total?
        tree_cnt = sum(self.gaps_per_tree.values())
        node_cnt = sum(self.gaps_per_node.values())
        # summary
        fmt = 'Gap degree {0:3n}: {1:7n} {2} ({3:5.2f}%)'
        print()
        print("*** Gap degree summary ***")
        print()
        print("%d trees, %d nodes" % (tree_cnt, node_cnt))
        print()
        print("Per tree:")
        for gapdeg in sorted(self.gaps_per_tree.keys()):
            print(fmt.format(gapdeg,
                             self.gaps_per_tree[gapdeg],
                             "trees",
                             (self.gaps_per_tree[gapdeg] / tree_cnt) * 100))
        print()
        print("Per node (non-terminals only):")
        for gapdeg in sorted(self.gaps_per_node.keys()):
            print(fmt.format(gapdeg,
                             self.gaps_per_node[gapdeg],
                             "nodes",
                             (self.gaps_per_node[gapdeg] / node_cnt * 100)))


def gap_degree(tree):
    """Return the maximal gap degree of the nodes in the given tree.
    """
    return max([gap_degree_node(subtree) for subtree in trees.preorder(tree)])


def has_gaps(tree):
    """Return true if the tree has gaps.
    """
    return gap_degree_node(tree) > 0


def gap_type(tree):
    """Return the gap type: source, pass, none (Maier & Lichte 2016).
    """
    if not trees.has_children(tree):
        return "none"
    terminals = trees.terminals(tree)
    pos = terminals[0].data['num']
    for terminal in terminals[1:]:
        if terminal.data['num'] > pos + 1:
            return "pass"
        pos += 1
    for child in trees.children(tree):
        if trees.has_children(child) and has_gaps(child):
            return "source"
    return "none"


def disco_order(tree, mode):
    """Return the continuous reordering of this tree (Maier and Lichte, 2016).
    Mode can be one of 'left', 'rightd'.
    """
    result = []
    ochildren = trees.children(tree)
    if len(ochildren) > 2:
        raise ValueError("tree must be binarized")
    if not trees.has_children(tree):
        return [tree]
    if len(ochildren) == 1:
        result = disco_order(ochildren[0], mode)
    if len(ochildren) == 2:
        left = ochildren[0]
        right = ochildren[1]
        if mode == "left":
            result = disco_order(left, mode)
            result.extend(disco_order(right, mode))
        elif mode == "rightd":
            if gap_type(tree) == "source":
                result = disco_order(right, mode)
                result.extend(disco_order(left, mode))
            else:
                result = disco_order(left, mode)
                result.extend(disco_order(right, mode))
        else:
            raise ValueError("unknown mode")
    return result


def scalar_(tree):
    """Return tree in scalar notation
    """
    children = trees.children(tree)
    dist = []
    const = []
    tag = None
    height = 0
    if len(children) == 0:
        tag = [tree.data['label']]
    elif len(children) == 1:
        raise ValueError("Unary chains must be removed before using this")
    elif len(children) == 2:
        children = trees.children(tree)
        dl, cl, tl, hl = scalar_(children[0])
        dr, cr, tr, hr = scalar_(children[1])
        height = max(hl, hr) + 1
        dist = dl + [h] + dr
        const = cl + [tree.data['label']] + cr
        tag = tl + tr
    else:
        raise ValueError("Trees must be binarized")
    return dist, const, tag, height


def scalar(tree):
    return scalar_(tree)


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('treeanalysis',
                                   usage='%(prog)s src task [options] ',
                                   formatter_class=argparse.
                                   RawDescriptionHelpFormatter,
                                   description='analysis of treebank trees')
    parser.add_argument('src', help='input file')
    parser.add_argument('task', help='task to perform')
    # # for the future
    # parser.add_argument('--params', nargs='+', metavar='P',
    #                     help='space separated list of task ' \
    #                         'parameters P of the form (default: ' \
    #                         '%(default)s)',
    #                     default=[])
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
    parser.add_argument('--usage', nargs=0, help='show detailed information ' \
                        'about available tasks and input format/options',
                        action=UsageAction)
    parser.set_defaults(func=run)
    return parser


class UsageAction(argparse.Action):
    """Custom action which shows extended help on available task
    options.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        title_str = misc.bold("%s help" % sys.argv[0])
        help_str = "\n\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n" \
                   % (misc.bold('available tasks: '),
                      misc.get_doc(TASKS),
                      misc.bold('available input formats: '),
                      misc.get_doc(treeinput.INPUT_FORMATS),
                      misc.bold('available input options: '),
                      misc.get_doc_opts(treeinput.INPUT_OPTIONS))
        print("\n%s%s" % (title_str, help_str))
        sys.exit()


def run(args):
    """Run the task on trees.
    """
    sys.stderr.write("reading from '%s' in format '%s' and encoding '%s'\n"
                     % (args.src, args.src_format, args.src_enc))
    sys.stderr.write("running %s\n" % args.task)
    cnt = 1
    task_instance = globals()[args.task]()
    for tree in getattr(treeinput,
                        args.src_format)(args.src, args.src_enc,
                                         **misc.options_dict \
                                         (args.src_opts)):
        tree = task_instance.run(tree)
        if cnt % 100 == 0:
            sys.stderr.write("\r%d" % cnt)
        cnt += 1
    task_instance.done()
    sys.stderr.write("\n")


TASKS = [GapDegree, PosTags, SentenceCount]
