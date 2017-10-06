"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for transition extraction.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function
import argparse
import sys
from collections import Counter
from . import trees, treeinput, treeanalysis, transform
from . import misc, transitionoutput


class Transition():
    def __init__(self, name):
        self.name = name

    def pretty_print(self):
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
            transitions.append(Transition("BINARY-%s-%s" % (headside, node.data["label"])))
        else:
            raise ValueError("trees must be binarized")
    return terminals, list(reversed(transitions))


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
        title_str = misc.bold("%s help" % sys.argv[0])
        help_str = "\n\n%s\n%s\n\n%s\n%s\n\n%s" \
                   + "\n%s\n\n%s\n%s\n\n%s\n%s" \
            % (misc.bold("%s\n%s\n" %
                         ('available transition types: ',
                          '=============================== ')),
               misc.get_doc_opts(TRANSTYPES),
               misc.bold("%s\n%s\n" %
                         ('available tree input formats: ',
                          '============================= ')),
               misc.get_doc(treeinput.INPUT_FORMATS),
               misc.bold("%s\n%s\n" %
                         ('available input options (trees): ',
                          '================================ ')),
               misc.get_doc_opts(treeinput.INPUT_OPTIONS),
               misc.bold("%s\n%s\n" %
                         ('available dest formats: ',
                          '======================= ')),
               misc.get_doc(transitionoutput.FORMATS),
               misc.bold("%s\n%s\n" %
                         ('available dest options: ',
                          '======================= ')),
               misc.get_doc_opts(transitionoutput.FORMAT_OPTIONS))
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
            print(args.transform)
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


TRANSTYPES = {'topdown': 'Top-down continuous.'}
