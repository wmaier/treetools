"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar input.

Author: Wolfgang Maier <maierw@hhu.de>
"""
import io
from collections import Counter
from . import misc, grammarconst


def rcg(src, src_enc, **opts):
    """Read rparse RCG format grammar.
    """
    lexicon = {}
    grammar = {}
    if 'lex_in_grammar' in opts:
       raise ValueError("Not supported for RCG format") 
    with io.open('%s.lex' % src) as lexfile:
        for line in lexfile:
            sp = line.strip().split()
            word = sp[0]
            for label, count in misc.grouper(2, sp[1:]):
                if not word in lexicon:
                    lexicon[word] = Counter([])
                for i in range(int(count)):
                    lexicon[word].update([label])
    with io.open('%s.rcg' % src) as gramfile:
        for line in gramfile:
            line = line.strip().split()
            count = int(line[0].split(':')[1])
            func = []
            raw_lin = []
            for pred in line[1:2] + line[3:]:
                paren = pred.find('(')
                label = grammarconst.label_strip_fanout(pred[:paren])
                func.append(label)
                raw_lin.append(pred[paren + 1:-1])
            func = tuple(func)
            # positions within rhs predicates
            rhspos = [0] * (len(raw_lin) - 1)
            lin = []
            for lhsarg in raw_lin[0].split(','):
                lin.append([])
                for lhsargel in lhsarg[1:-1].split(']['):
                    for i, rhspred in enumerate(raw_lin[1:]):
                        rhsargs = rhspred.split(',')
                        if len(rhsargs) == rhspos[i]:
                            continue
                        rhsarg = rhsargs[rhspos[i]]
                        rhsargel = rhsarg[1:-1]
                        if rhsargel == lhsargel:
                            lin[-1].append((i, rhspos[i]))
                            rhspos[i] += 1
                            break
                lin[-1] = tuple(lin[-1])
            lin = tuple(lin)
            if not func in grammar:
                grammar[func] = {}
            if not lin in grammar[func]:
                grammar[func][lin] = {}
            grammar[func][lin][grammarconst.DEFAULT_VERT] = count
    return grammar, lexicon


FORMATS = [rcg]
FORMAT_OPTIONS = {'lex_in_grammar' : 'Grammar contains lexical rules'}
