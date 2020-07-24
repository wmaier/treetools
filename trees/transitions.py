"""treetools: Tools for transforming treebank trees.

This module provides functions and classes for transition extraction.

Author: Wolfgang Maier <maierw@hhu.de>
"""
import argparse
import sys
from . import trees, treeinput, transform
from . import misc, transitionoutput


class Transition():
    def __init__(self, name):
        self.name = name

    def pretty_print(self):
        return self.name

    def __str__(self):
        return self.name


def topdown(tree):
    """Extract transitions topdown for continuous trees.
    """
    terminals = [(terminal.data['word'], terminal.data['label'])
                 for terminal in trees.terminals(tree)]
    transitions = []
    for node in trees.preorder(tree):
        children = trees.children(node)
        if len(children) == 0:
            transitions.append(Transition("SHIFT"))
        elif len(children) == 1:
            transitions.append(Transition("UNARY-%s" % node.data["label"]))
        elif len(children) == 2:
            if 'head' not in children[0].data:
                raise ValueError("heads are supposed to be marked")
            headside = "LEFT" if children[0].data['head'] else "RIGHT"
            transitions.append(Transition("BINARY-%s-%s" %
                                          (headside, node.data["label"])))
        else:
            raise ValueError("trees must be binarized")
    print(terminals, [str(t)
                      for t in list(reversed(transitions))], file=sys.stderr)
    return terminals, list(reversed(transitions))


def _inorder(tree):
    """Recursive inorder transition
    """
    transitions = []
    c = trees.children(tree)
    if len(trees.children(c[0])) == 0:
        transitions.append(Transition("SHIFT"))
    else:
        transitions.extend(_inorder(c[0]))
    transitions.append(Transition("PJ-{}".format(tree.data['label'])))
    for child in c[1:]:
        if len(trees.children(child)) == 0:
            transitions.append(Transition("SHIFT"))
        else:
            transitions.extend(_inorder(child))
    transitions.append(Transition("REDUCE"))
    return transitions


def inorder(tree):
    """Extract inorder transitions for continuous trees.
    """
    terminals = [(terminal.data['word'], terminal.data['label'])
                 for terminal in trees.terminals(tree)]
    transitions = _inorder(tree)
    return terminals, transitions


def gap(tree):
    """GAP transition parsing (Coavoux & Crabbe)
    """
    terminals = [(terminal.data['word'], terminal.data['label'])
                  for terminal in trees.terminals(tree)]
    transitions = []
    b = [terminal for terminal in trees.terminals(tree)]
    d = []
    s = []
    while True:
        if len(s) > 0 and len(d) > 0 and d[0].parent == s[0].parent:
            # REDUCE
            p = s[0].parent
            if 'head' not in s[0].data or 'head' not in d[0].data:
                raise ValueError("heads are supposed to be marked")
            headside = "LEFT" if s[0].data['head'] else "RIGHT"
            t = Transition("R-{}-{}".format(headside, p.data['label']))
            transitions.append(t)
            s = s[1:]
            d = d[1:]
            while len(d) > 0:
                s = [d.pop(0)] + s
            d = [p] + d
        elif len(d) > 0 and any([n.parent == d[0].parent for i,n in enumerate(s)]):
            # GAP
            for i, n in enumerate(s):
                if n.parent == d[0].parent:
                    for j in range(i):
                        d.append(s.pop(0))
                        t = Transition("GAP")
                        transitions.append(t)
                    break
        else:
            t = Transition("SHIFT")
            transitions.append(t)
            while len(d) > 0:
                s = [d.pop(0)] + s
            d = [b.pop(0)] + d
        if len(s) == 0 and len(b) == 0 and len(d) == 1:
            break
        # check for unary
        while len(d) > 0 and d[0].parent and len(trees.children(d[0].parent)) == 1:
            t = Transition("UNARY-{}".format(d[0].parent.data['label']))
            transitions.append(t)
            d[0] = d[0].parent
    return terminals, transitions


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('transitions',
                                   usage='%(prog)s src dest '
                                   'transtype [options] ',
                                   formatter_class=argparse.
                                   RawDescriptionHelpFormatter,
                                   description='transition extraction from'
                                   ' treebank trees')
    parser.add_argument('src', help='input file')
    parser.add_argument('dest', help='prefix of output files')
    parser.add_argument('transtype', metavar='T', choices=[t for t in TRANSTYPES],
                        help='type of transitions (default: %(default)s)',
                        default='topdown')
    parser.add_argument('--transform', metavar='TS', choices=[fun.__name__ for fun in
                                                              transform.TRANSFORMATIONS],
                        nargs='+',
                        help='tree transformations to apply before extraction',
                        default=[])
    parser.add_argument('--transformparams', metavar='TSP',
                        nargs='+', help='tree transformations parameters',
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
                        help='grammar format (default: %(default)s)',
                        default='plain')
    parser.add_argument('--dest-enc', metavar='ENCODING',
                        help='grammar encoding (default: %(default)s)',
                        default='utf-8')
    parser.add_argument('--dest-opts', nargs='+', metavar='O',
                        help='space separated list of options O for writing '
                        'the transitions of the form key:value '
                        '(default: %(default)s)',
                        default=[])
    parser.add_argument('--verbose', action='store_true', help='More verbose '
                        'messages', default=False)
    parser.add_argument('--usage', nargs=0, help='show detailed information '
                        'about available tasks and input format/options',
                        action=UsageAction)
    parser.set_defaults(func=run)
    return parser


class UsageAction(argparse.Action):
    """Custom action which shows extended help on available options.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        title_str = misc.bold("{} help".format(sys.argv[0]))
        help_str = "\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}".\
            format(misc.make_headline("available transition types:"), misc.get_doc_opts(TRANSTYPES),
                misc.make_headline("available tree input formats:"), misc.get_doc(treeinput.INPUT_FORMATS),
                misc.make_headline("available tree input opts:"), misc.get_doc_opts(treeinput.INPUT_OPTIONS),
                misc.make_headline("available output formats:"), misc.get_doc(transitionoutput.FORMATS),
                misc.make_headline("available output opts:"), misc.get_doc_opts(transitionoutput.FORMAT_OPTIONS))
        print("\n%s%s" % (title_str, help_str))
        sys.exit()


def run(args):
    """Run the transition extraction.
    """
    print("reading from '%s' in format '%s' and encoding '%s'"
          % (args.src, args.src_format, args.src_enc), file=sys.stderr)
    tree_inputformats = [fun.__name__ for fun in treeinput.INPUT_FORMATS]
    transitions = []
    if args.src_format in tree_inputformats:
        print("extracting transitions (%s)" % args.transtype, file=sys.stderr)
        cnt = 1
        for tree in getattr(treeinput,
                            args.src_format)(args.src, args.src_enc,
                                             **misc.options_dict
                                             (args.src_opts)):
            for algorithm in args.transform:
                print(algorithm)
                tree = getattr(transform, algorithm)(
                    tree, **misc.options_dict(args.transformparams))
            sentence, trans = globals()[args.transtype](tree)
            transitions.append((sentence, trans))
            if cnt % 100 == 0:
                print("\r%d" % cnt, end="", file=sys.stderr)
            cnt += 1
    else:
        raise ValueError("Specify input format %s" % args.src_format)
    print("\n", file=sys.stderr)
    sys.stderr.write("\nwriting transitions in format '%s', encoding '%s', to '%s'"
                     % (args.dest_format, args.dest_enc, args.dest))
    sys.stderr.write("\n")
    getattr(transitionoutput, args.dest_format)(transitions, args.dest, args.dest_enc,
                                                **misc.options_dict(args.dest_opts))
    print("\n", file=sys.stderr)
    sys.exit()


TRANSTYPES = {'topdown': 'Top-down continuous',
              'inorder': 'Inorder continuous',
              'gap': 'Gap discontinuous'}
