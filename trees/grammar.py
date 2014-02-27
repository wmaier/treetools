""" 
treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar extraction

Author: Wolfgang Maier <maierw@hhu.de>
"""
import argparse
import sys
from . import trees, treeinput, misc


PRAGMA = ":"
RULE = ":"
RULEARROW = "<-"
LINEARIZATION = "="
SEQUENCE = "->"


def make_grammar():
    """Prepare an empty grammar dict.
    """
    grammar = {}
    grammar['funcs'] = {}
    grammar['lindef'] = {}
    return grammar


def extract(tree, grammar, **opts):
    """Extract a PMCFG. Output is done later in possibly different formats.
    """
    tree['arity'] = len(trees.terminal_blocks(tree))
    tree['terminals'] = trees.terminals(tree)
    func_cnt = 0
    lindef_cnt = 0
    for subtree in trees.preorder(tree):
        if trees.has_children(subtree):
            linearization = []
            lhs = "%s%d" % (subtree['label'], subtree['arity'])
            rhses = []
            for i, child in enumerate(trees.children(subtree)):
                child['terminals'] = trees.terminals(child)
                argpos = 0
                for j, term in enumerate(child['terminals'][:-1]):
                    if child['terminals'][j + 1]['num'] \
                       > (child['terminals'][j]['num'] + 1):
                        linearization.append((i, argpos))
                        argpos += 1
                linearization.append((i, argpos))
                child['arity'] = argpos + 1
                rhses.append("%s%d" % (child['label'], child['arity']))
            func = tuple([lhs] + rhses)
            func_id = None
            if not func in grammar['funcs']:
                func_id = func_cnt
                func_cnt += 1
                grammar['funcs'][func_id] = { 'func' : func , 'count' : 0 }
                grammar['funcs'][func] = func_id
            else:
                func_id = grammar['funcs'][func]
            grammar['funcs'][func_id]['count'] += 1
            linearization_ids = []
            for lin in linearization:
                lindef_id = None
                if not lin in grammar['lindef']:
                    lindef_id = lindef_cnt
                    lindef_cnt += 1
                    grammar['lindef'][lindef_id] = { 'lindef' : lin }
                    grammar['lindef'][lin] = lindef_id
                else:
                    lindef_id = grammar['lindef'][lin]
            linearization_ids = tuple(linearization_ids)
            print grammar


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('extract', 
                                   usage='%(prog)s src [options] ', 
                                   formatter_class=argparse. 
                                   RawDescriptionHelpFormatter,
                                   description='grammar extraction from treebank trees')
    parser.add_argument('src', help='input file')
    parser.add_argument('--params', nargs='+', metavar='P',
                        help='params P for grammar extraction in form k:v' \
                            '(default: %(default)s)', default=[])
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
                        help='grammar format (default: %(default)s)', 
                        default='pmcfg')
    parser.add_argument('--dest-enc', metavar='ENCODING', 
                        help='grammar encoding (default: %(default)s)', 
                        default='utf-8')
    parser.add_argument('--dest-opts', nargs='+', metavar='O',
                        help='space separated list of options O for writing ' \
                            'the grammar of the form key:value ' \
                            '(default: %(default)s)', 
                        default=[])
    parser.add_argument('--usage', nargs=0, help='show detailed information ' \
                        'about available tasks and input format/options', 
                        action=UsageAction)
    parser.set_defaults(func=run)
    return parser


class UsageAction(argparse.Action):
    """Custom action which shows extended help on available options.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        title_str = misc.bold("%s help" % sys.argv[0])
        help_str = "\n\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n" \
            % (misc.bold('extraction parameters: '), 
               misc.get_doc_opts(grammar.PARAMS),
               misc.bold('available input formats: '),
               misc.get_doc(treeinput.INPUT_FORMATS),
               misc.bold('available input options: '),
               misc.get_doc_opts(treeinput.INPUT_OPTIONS),
               misc.bold('available dest formats: '),
               misc.get_doc(grammar.FORMATS),
               misc.bold('available dest options: '),
               misc.get_doc_opts(grammar.FORMAT_OPTIONS))
        print("\n%s%s" % (title_str, help_str))
        sys.exit()


def run(args):
    """Run the grammar extraction.
    """
    sys.stderr.write("reading from '%s' in format '%s' and encoding '%s'\n" 
                     % (args.src, args.src_format, args.src_enc))
    sys.stderr.write("extracting grammar\n")
    grammar = make_grammar()
    cnt = 1
    for tree in getattr(treeinput, 
                        args.src_format)(args.src, args.src_enc, 
                                         **misc.options_dict \
                                         (args.src_opts)):
        extract(tree, grammar, **misc.options_dict(args.params))
        if cnt % 100 == 0:
            sys.stderr.write("\r%d" % cnt)
        cnt += 1
    sys.stderr.write("writing grammar in format '%s', encoding '%s'\n"
                     % (args.dest_format, args.dest_enc))
    print grammar
    sys.stderr.write("\n")


PARAMS = {}
FORMATS = ['pmcfg']
FORMAT_OPTIONS = {}
