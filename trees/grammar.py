"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar extraction.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function
import argparse
import sys
from collections import Counter
from . import analyze, trees, treeinput, misc, grammaroutput, grammaranalysis


# PMCFG format constants
PRAGMA = ":"
RULE = ":"
RULEARROW = "<-"
LINEARIZATION = "="
SEQUENCE = "->"
# RCG format constants
RCG_RULEARROW = "-->"
# other constants
DEFAULT_BINLABEL = "@"
DEFAULT_BINSUFFIX = "X"
DEFAULT_MARKOV_HORIZONTALSEP = "-"
DEFAULT_MARKOV_VERTICALSEP = "^"
DEFAULT_VERT = "VERT"


class LabelGenerator(object):
    """Generator which delivers unique binarization labels. For
    other kinds of labels, overwrite next().
    """
    def __init__(self, *args, **kwargs):
        """Allow parameters, also from subclasses.
        """
        self.args = args
        self.kwargs = kwargs
        self.n = 0

    def next(self, **params):
        """Deliver next unique label (wihtout fan-out)
        """
        self.n += 1
        return "%s%d%s" % (DEFAULT_BINLABEL, self.n, DEFAULT_BINSUFFIX)


class MarkovLabelGenerator(LabelGenerator):
    """Generator which delivers binarization lables with markovization
    information.
    """
    def next(self, **params):
        vert = ""
        if self.kwargs['p']['v'] > 0:
            for i, _ in enumerate(params['vert']):
                if not i < self.kwargs['p']['v']:
                    break
                vert += "%s%s" % (DEFAULT_MARKOV_VERTICALSEP,
                                  params['vert'][i])
        horiz = ""
        if self.kwargs['p']['h'] > 0:
            i = params['pos'] + 1
            cnt = 0
            while i >= 1 and cnt < self.kwargs['p']['h']:
                i -= 1
                cnt += 1
                if 'nofanout' in self.kwargs['p']:
                    horiz += "%s%s" % (DEFAULT_MARKOV_HORIZONTALSEP, \
                                       params['func'][i + 1])
                else:
                    horiz += "%s%s%d" % (DEFAULT_MARKOV_HORIZONTALSEP, \
                                         params['func'][i + 1],
                                         params['fanout'][i + 1])
        return "%s%s%s%s" % (DEFAULT_BINLABEL, vert, horiz, DEFAULT_BINSUFFIX)


def linsub(lin, src, dest, replace):
    """Linearization vector substitution, operations 1.-3. of Maier (2013),
    p. 115. 'src' and 'dest' are functions. Creates a new two-dimensional list
    from a given two-dimensional list with linearization definitions. For all
    elements for which dest holds, the corresponding element is replaced with
    yield of dest for this element. If replace is true, then replacement is
    not performed if the last call to dest has yielded the same value. If dest
    yields None (operation 2.), a new sublist is introduced.
    """
    result = []
    # other than in Maier (2013) we keep track of the position
    # of each linearization vector element *within* an RHS non-term
    rhsargpos = Counter([])
    # iterate through first dimension of list (lhs args)
    for arg in lin:
        repl_arg = []
        # iterate through second dimension of list (lhs arg elements)
        for (rhspos, _) in arg:
            # if we have a replacement candidate
            if src(rhspos):
                this_dest = dest(rhspos)
                # if replacement is not None
                if not this_dest == None:
                    # if we don't want subsequent identical values
                    # in the result list, append if the current sublist
                    # was empty or if the last appended element in the sublist
                    # was not the same as now
                    if replace:
                        if len(repl_arg) == 0 \
                           or not repl_arg[-1][0] == this_dest:
                            rhsargpos.update([this_dest])
                            repl_arg.append((this_dest,
                                             rhsargpos[this_dest] - 1))
                    else:
                        # otherwise append replacement
                        rhsargpos.update([this_dest])
                        repl_arg.append((this_dest, rhsargpos[this_dest] - 1))
                else:
                    # if replacement is None, don't do replacement
                    # but create new sublist
                    if not len(repl_arg) == 0:
                        result.append(tuple(repl_arg))
                    repl_arg = []
            else:
                rhsargpos.update([rhspos])
                repl_arg.append((rhspos, rhsargpos[rhspos] - 1))
        if not len(repl_arg) == 0:
            result.append(tuple(repl_arg))
    return tuple(result)


def binarize_rule(func, lin, rule_cnt, vert, grammar, label_gen, result):
    """Left-to-right binarization of a single rule.
    """
    fanout = grammaranalysis.fan_out(lin)
    rule_cnt = sum(grammar[func][lin].values())
    if len(func[1:]) <= 2:
        if not func in result:
            result[func] = {}
        if not lin in result[func]:
            result[func][lin] = {}
        result[func][lin][DEFAULT_VERT] = rule_cnt
    else:
        this_lin = lin
        sub_lin = linsub(lin, lambda x: x > 0, lambda x: 1, True)
        bin_label = label_gen.next(func=func, pos=0, vert=vert, fanout=fanout)
        bin_func = tuple([func[0], func[1], bin_label])
        if not bin_func in result:
            result[bin_func] = {}
        if not sub_lin in result[bin_func]:
            result[bin_func][sub_lin] = {}
        result[bin_func][sub_lin][DEFAULT_VERT] = rule_cnt
        for i in range(1, len(func) - 3):
            this_lin = linsub(this_lin, lambda x: x >= 0,
                              lambda x: x - 1, False)
            this_lin = linsub(this_lin, lambda x: x == -1,
                              lambda x: None, False)
            sub_lin = linsub(this_lin, lambda x: x > 0, lambda x: 1, True)
            next_label = label_gen.next(func=func, pos=i, vert=vert,
                                        fanout=fanout)
            bin_func = tuple([bin_label, func[i + 1], next_label])
            bin_label = next_label
            if not bin_func in result:
                result[bin_func] = {}
            if not sub_lin in result[bin_func]:
                result[bin_func][sub_lin] = {}
            result[bin_func][sub_lin][DEFAULT_VERT] = rule_cnt
        bin_func = tuple([bin_label, func[-2], func[-1]])
        this_lin = linsub(this_lin, lambda x: x >= 0, lambda x: x - 1, False)
        this_lin = linsub(this_lin, lambda x: x == -1, lambda x: None, False)
        if not bin_func in result:
            result[bin_func] = {}
        if not this_lin in result[bin_func]:
            result[bin_func][this_lin] = {}
        result[bin_func][this_lin][DEFAULT_VERT] = rule_cnt


def reordering_none(func, lin):
    """No reordering.
    """
    raise ValueError("not yet implemented")


def reordering_optimal(func, lin):
    """Rule-optimal binarization (Kallmeyer 2010).
    """
    raise ValueError("not yet implemented")


def binarize(grammar, **args):
    """Grammar binarization.
    """
    result = {}
    # with markovization?
    if args['markov_opts'] is not None:
        nofanout = 'nofanout' in args['markov_opts']
        nf_vert = []
        if nofanout:
            # collapse counts for vertical context in which labels have
            # their fanouts stripped
            for func in grammar:
                for lin in grammar[func]:
                    for vert in grammar[func][lin]:
                        nf_vert.append(tuple([trees.label_strip_fanout(label)
                                              for label in vert]))
            nf_vert_c = Counter(nf_vert)
        label_gen = MarkovLabelGenerator(p=args['markov_opts'])
        for func in grammar:
            for lin in grammar[func]:
                for vert in grammar[func][lin]:
                    rule_cnt = grammar[func][lin][vert]
                    if nofanout:
                        # then use the corresponding counts/contexts
                        vert = tuple([trees.label_strip_fanout(label)
                                      for label in vert])
                        rule_cnt = nf_vert_c[vert]
                    func, lin = args['reordering'](func, lin)
                    binarize_rule(func, lin, rule_cnt, vert,
                                  grammar, label_gen, result)
    else:
        # without markovization
        label_gen = LabelGenerator()
        vert = DEFAULT_VERT
        for func in grammar:
            for lin in grammar[func]:
                rule_cnt = sum(grammar[func][lin].values())
                func, lin = args['reordering'](func, lin)
                binarize_rule(func, lin, rule_cnt, vert,
                              grammar, label_gen, result)
    return result


def extract(tree, grammar, lexicon):
    """Extract a PMCFG. We remember "bare" CFG productions, together with
    possible linearizations, together with vertical contexts from the tree
    (for later markovization). So far no extraction of rules from pre-terminal
    level.
    """
    for subtree in trees.preorder(tree):
        if trees.has_children(subtree):
            # map terminal indices to the positions of the rhs elements
            # by which they are covered, furthermore build bare rule
            term_map = {}
            func = [subtree.data['label']]
            for i, child in enumerate(trees.children(subtree)):
                func.append(child.data['label'])
                for terminal in trees.terminals(child):
                    term_map[terminal.data['num']] = i
            func = tuple(func)
            # build linearization
            lin = []
            # position within rhs element
            rhs_argpos = [0] * (len(func) - 1)
            # one lhs argument per block in the tree
            for block in trees.terminal_blocks(subtree):
                lin.append([])
                # loop through terminals
                for terminal in block:
                    rhs_pos = term_map[terminal.data['num']]
                    # append the number of the rhs element which covers
                    # the current terminal if nothing has been appended yet
                    # or if the current element is different from the last one
                    # appended
                    if len(lin[-1]) == 0 or not lin[-1][-1][0] == rhs_pos:
                        lin[-1].append((rhs_pos, rhs_argpos[rhs_pos]))
                        rhs_argpos[rhs_pos] += 1
                # make the argument a tuple
                lin[-1] = tuple(lin[-1])
            lin = tuple(lin)
            # vertical context for markovization (with fan-outs)
            vert = tuple(["%s%d" % (dom.data['label'],
                                    analyze.gap_degree_node(dom) + 1)
                          for dom in trees.dominance(subtree)])
            if not func in grammar:
                grammar[func] = {}
            if not lin in grammar[func]:
                grammar[func][lin] = {}
            if not vert in grammar[func][lin]:
                grammar[func][lin][vert] = 0
            grammar[func][lin][vert] += 1
        else:
            # lexicon
            word = subtree.data['word']
            label = subtree.data['label']
            if not word in lexicon:
                lexicon[word] = Counter([])
            lexicon[word].update([label])
    return grammar


def add_parser(subparsers):
    """Add an argument parser to the subparsers of treetools.py.
    """
    parser = subparsers.add_parser('grammar',
                                   usage='%(prog)s src dest ' \
                                   'gramtype [options] ',
                                   formatter_class=argparse.
                                   RawDescriptionHelpFormatter,
                                   description='grammar extraction from' \
                                   ' treebank trees')
    parser.add_argument('src', help='input file')
    parser.add_argument('dest', help='prefix of output files')
    parser.add_argument('gramtype', metavar='T', choices=[t for t in GRAMTYPES],
                        help='type of output grammar (default: %(default)s)',
                        default='treebank')
    parser.add_argument('--markov', metavar='M', nargs='+',
                        help='markovization parameters M as pairs key:value' \
                        ' (default: %(default)s) (at least one must be '\
                        ' specified. Deterministic binarization' \
                        ' if option not present.')
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
        help_str = "\n\n%s\n%s\n\n%s\n%s\n\n%s\n%s\n\n%s\n" \
                   "%s\n\n%s\n%s\n\n%s\n%s" \
            % (misc.bold("%s\n%s\n" %
                         ('available grammar output types: ',
                          '=============================== ')),
               misc.get_doc_opts(GRAMTYPES),
               misc.bold("%s\n%s\n" %
                         ('available markovization parameters: ',
                          '=================================== ')),
               misc.get_doc_opts(MARKOVPARAMS),
               misc.bold("%s\n%s\n" %
                         ('available input formats: ',
                          '======================== ')),
               misc.get_doc(treeinput.INPUT_FORMATS),
               misc.bold("%s\n%s\n" %
                         ('available input options: ',
                          '======================== ')),
               misc.get_doc_opts(treeinput.INPUT_OPTIONS),
               misc.bold("%s\n%s\n" %
                         ('available dest formats: ',
                          '======================= ')),
               misc.get_doc(grammaroutput.FORMATS),
               misc.bold("%s\n%s\n" %
                         ('available dest options: ',
                          '======================= ')),
               misc.get_doc_opts(grammaroutput.FORMAT_OPTIONS))
        print("\n%s%s" % (title_str, help_str))
        sys.exit()


def run(args):
    """Run the grammar extraction.
    """
    print("reading from '%s' in format '%s' and encoding '%s'"
          % (args.src, args.src_format, args.src_enc), file=sys.stderr)
    print("extracting grammar (%s)" % args.gramtype, file=sys.stderr)
    grammar = {}
    lexicon = {}
    cnt = 1
    for tree in getattr(treeinput,
                        args.src_format)(args.src, args.src_enc,
                                         **misc.options_dict \
                                         (args.src_opts)):
        extract(tree, grammar, lexicon)
        if cnt % 100 == 0:
            print("\r%d" % cnt, end="", file=sys.stderr)
        cnt += 1
    if not args.gramtype == 'treebank':
        markov_opts = None
        if args.markov is not None:
            markov_opts = misc.options_dict(args.markov)
            if not 'v' in markov_opts:
                markov_opts['v'] = 1
            if not 'h' in markov_opts:
                markov_opts['h'] = 2
            print("markovization with options %s" % str(markov_opts),
                  file=sys.stderr)
        reordering = None
        if args.gramtype == 'leftright':
            reordering = reordering_none
        elif args.gramtype == 'optimal':
            reordering = reordering_optimal
        grammar = binarize(grammar, reordering=reordering,
                           markov_opts=markov_opts)
    sys.stderr.write("\nwriting grammar in format '%s', encoding '%s', to '%s'"
                     % (args.dest_format, args.dest_enc, args.dest))
    sys.stderr.write("\n")
    getattr(grammaroutput, args.dest_format) \
        (grammar, lexicon, args.dest,
         args.dest_enc,
         **misc.options_dict(args.dest_opts))
    print("\n", file=sys.stderr)


GRAMTYPES = {'treebank' : 'Plain treebank grammar',
             'leftright' : 'Simple left-to-right binarization',
             'optimal' : 'Optimal binarization'}
MARKOVPARAMS = {'v' : 'vertical markovization (default 1)',
                'h' : 'horizontal markovization (default 2)',
                'nofanout' : 'No fan-out on markovization symbols in ' \
                'binarization non-terminals (default false)'}
