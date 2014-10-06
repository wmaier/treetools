"""
treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar output.

Author: Wolfgang Maier <maierw@hhu.de>
"""
import io
import sys
from itertools import chain
from collections import defaultdict
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
from . import grammarconst, grammaranalysis


BRACKETS = ["(", ")"]


def lopar(gram, lexicon, dest, dest_enc, **params):
    """Write grammar, lexicon and oc files in LoPar format.
    """
    if not grammaranalysis.is_contextfree(gram):
        raise ValueError("must be PCFG to be written in LoPar format.")
    # look for start symbols
    lhses = set([f[0] for f in gram])
    rhses = set(chain.from_iterable([f[1:] for f in gram]))
    startsymbols = {symbol : 0 for symbol in lhses - rhses}
    # open class: cat -> counter, no effort to distinguish closed from open
    oc_lower = defaultdict(int)
    oc_upper = defaultdict(int)
    with io.open("%s.gram" % dest, 'w', encoding=dest_enc) as gram_stream, \
         io.open("%s.lex" % dest, 'w', encoding=dest_enc) as lex_stream, \
         io.open("%s.start" % dest, 'w', encoding=dest_enc) as start_stream, \
         io.open("%s.oc" % dest, 'w', encoding=dest_enc) as ocl_stream, \
         io.open("%s.OC" % dest, 'w', encoding=dest_enc) as ocu_stream:
        for func in gram:
            for lin in gram[func]:
                count = sum(gram[func][lin].values())
                # count start symbols
                if func[0] in startsymbols:
                    startsymbols[func[0]] += count
                lhs = u"%s" % func[0]
                rhs = ' '.join([u"%s" % func[i + 1]
                                for i in range(len(func[1:]))])
                gram_stream.write(u"%d %s %s\n" % (count, lhs, rhs))
        for word in lexicon:
            if any(c in BRACKETS for c in word):
                sys.stderr.write("brackets seem to not have been replaced, " \
                                 "may garble parser output: %s\n" % word)
            # count oc stuff
            if word[0].isupper():
                for tag in lexicon[word]:
                    oc_upper[tag] += lexicon[word][tag]
            else:
                for tag in lexicon[word]:
                    oc_lower[tag] += lexicon[word][tag]
            tags = ["%s %d" % (tag, lexicon[word][tag])
                    for tag in lexicon[word]]
            lex_stream.write(u"%s\t%s\n" % (word, ' '.join(tags)))
        for symbol in startsymbols:
            start_stream.write(u"%s %d\n" % (symbol, startsymbols[symbol]))
        for tag in oc_lower:
            ocl_stream.write(u"%s %d\n" % (tag, oc_lower[tag]))
        for tag in oc_upper:
            ocu_stream.write(u"%s %d\n" % (tag, oc_upper[tag]))


def pmcfg(gram, lexicon, dest, dest_enc, **params):
    """Write grammar in pmcfg format, with count field. Lexicon
    in LoPar format or as grammar productions if lex_in_grammar is specified.
    """
    lindef_to_id = {}
    id_to_lindef = {}
    func_id = 1
    lindef_id = 1
    if 'lex_in_grammar' in params:
        for word in lexicon:
            if any(c in BRACKETS for c in word):
                sys.stderr.write("brackets seem to not have been replaced, " \
                                 "may garble parser output: %s\n" % word)
            for (tag, count) in [(tag, lexicon[word][tag])
                        for tag in lexicon[word]]:
                func = (tag, word)
                if not func in gram:
                    gram[func] = {}
                lin = (((0, 0),),)
                if lin in gram[func]:
                    count = gram[func][lin][(grammarconst.DEFAULT_VERT)] \
                            + count
                else:
                    gram[func][lin] = {(grammarconst.DEFAULT_VERT) : 0}
                gram[func][lin][grammarconst.DEFAULT_VERT] \
                    = count
    with io.open("%s.pmcfg" % dest, 'w', encoding=dest_enc) as dest_stream:
        for func in gram:
            for lin in gram[func]:
                count = sum(gram[func][lin].values())
                dest_stream.write(u" fun%d %s %s %s %s\n"
                                  % (func_id, grammarconst.RULE, func[0],
                                     grammarconst.RULEARROW,
                                     ' '.join(func[1:])))
                dest_stream.write(u" fun%d %s" % (func_id,
                                                  grammarconst.LINEARIZATION))
                for lindef in lin:
                    if not lindef in lindef_to_id:
                        lindef_to_id[lindef] = lindef_id
                        id_to_lindef[lindef_id] = lindef
                        lindef_id += 1
                    dest_stream.write(u" s%s" % lindef_to_id[lindef])
                dest_stream.write(u"\n")
                dest_stream.write(u" fun%d %d\n" % (func_id, count))
                func_id += 1
        for lindef_id in sorted(id_to_lindef, key=int):
            lindef = ' '.join(["%d:%d" % (i, j) for (i, j)
                               in id_to_lindef[lindef_id]])
            dest_stream.write(u" s%s %s %s\n" % (lindef_id,
                                                 grammarconst.SEQUENCE,
                                                 lindef))
    if not 'lex_in_grammar' in params:
        with io.open("%s.lex" % dest, 'w', encoding=dest_enc) as lex_stream:
            for word in lexicon:
                if any(c in BRACKETS for c in word):
                    sys.stderr.write("brackets not replaced, " \
                                     "may garble parser output: %s\n" % word)
                tags = ["%s %d" % (tag, lexicon[word][tag])
                        for tag in lexicon[word]]
                lex_stream.write(u"%s\t%s\n" % (word, ' '.join(tags)))


def rcg(gram, lexicon, dest, dest_enc, **params):
    """Write grammar in rparse rcg format, with count field. Lexicon
    in LoPar format or as grammar productions if lex_in_grammar is specified.
    """
    if 'lex_in_grammar' in params:
        for word in lexicon:
            if any(c in BRACKETS for c in word):
                sys.stderr.write("brackets seem to not have been replaced, " \
                                 "may garble parser output: %s\n" % word)
            for (tag, count) in [(tag, lexicon[word][tag])
                        for tag in lexicon[word]]:
                func = (tag, word)
                if not func in gram:
                    gram[func] = {}
                lin = (((0, 0),),)
                if lin in gram[func]:
                    count = gram[func][lin][(grammarconst.DEFAULT_VERT)] \
                            + count
                else:
                    gram[func][lin] = {(grammarconst.DEFAULT_VERT) : 0}
                gram[func][lin][grammarconst.DEFAULT_VERT] \
                    = count
    with io.open("%s.rcg" % dest, 'w', encoding=dest_enc) as dest_stream:
        for func in gram:
            for lin in gram[func]:
                count = sum(gram[func][lin].values())
                varcnt = 0
                lhsargs = StringIO()
                lhsarity = 1
                rhsargs = defaultdict(dict)
                rhsarity = defaultdict(int)
                for i, arg in enumerate(lin):
                    if not i == 0:
                        lhsargs.write(u",")
                        lhsarity += 1
                    for var in arg:
                        lhsargs.write(u"[%d]" % varcnt)
                        rhsargs[var[0]][var[1]] = varcnt
                        varcnt += 1
                rhsargs = [rhsargs[i] for i in sorted(rhsargs, key=int)]
                for i, rhs_el in enumerate(rhsargs):
                    rhsargs[i] = ','.join([u"[%d]" % rhs_el[pos] for pos
                                          in sorted(rhs_el, key=int)])
                    rhsarity[i] = len(rhs_el)
                lhs = u"%s%d(%s)" % (func[0], lhsarity, lhsargs.getvalue())
                lhsargs.close()
                rhs = ' '.join([u"%s%d(%s)" % (func[i + 1], rhsarity[i],
                                              rhsargs[i])
                                for i in range(len(func[1:]))])
                dest_stream.write(u"C:%d %s %s %s\n"
                                  % (count, lhs, grammarconst.RCG_RULEARROW,
                                     rhs))
    if not 'lex_in_grammar' in params:
        with io.open("%s.lex" % dest, 'w', encoding=dest_enc) as lex_stream:
            for word in lexicon:
                if any(c in BRACKETS for c in word):
                    sys.stderr.write("brackets not replaced, " \
                                     "may garble parser output: %s\n" % word)
                tags = ["%s %d" % (tag, lexicon[word][tag])
                        for tag in lexicon[word]]
                lex_stream.write(u"%s\t%s\n" % (word, ' '.join(tags)))


FORMATS = [pmcfg, rcg, lopar]
FORMAT_OPTIONS = {'lex_in_grammar' : 'Lexicon as grammar rules'}
