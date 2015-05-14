"""
treetools: Tools for transforming treebank trees.

transformations: constants and utilities

Author: Wolfgang Maier <maierw@hhu.de>
"""
import itertools
from . import trees

# Head rules for PTB (WSJ) from Collins (1999, p. 240)
HEAD_RULES_PTB = {
    'adjp' : [('left-to-right', 'nns qp nn $ advp jj vbn vbg adjp jjr np jjs dt fw rbr rbs sbar rb')],
    'advp' : [('right-to-left', 'rb rbr rbs fw advp to cd jjr jj in np jjs nn')],
    'conjp' : [('right-to-left', 'cc rb in')],
    'frag' : [('right-to-left', '')],
    'intj' : [('left-to-right', '')],
    'lst' : [('right-to-left', 'ls :')],
    'nac' : [('left-to-right', 'nn nns nnp nnps np nac ex $ cd qp prp vbg jj jjs jjr adjp fw')],
    'pp' : [('right-to-left', 'in to vbg vbn rp fw')],
    'prn' : [('left-to-right', '')],
    'prt' : [('right-to-left', 'rp')],
    'qp' : [('left-to-right', ' $ in nns nn jj rb dt cd ncd qp jjr jjs')],
    'rrc' : [('right-to-left', 'vp np advp adjp pp')],
    's' : [('left-to-right', ' to in vp s sbar adjp ucp np')],
    'sbar' : [('left-to-right', 'whnp whpp whadvp whadjp in dt s sq sinv sbar frag')],
    'sbarq' : [('left-to-right', 'sq s sinv sbarq frag')],
    'sinv' : [('left-to-right', 'vbz vbd vbp vb md vp s sinv adjp np')],
    'sq' : [('left-to-right', 'vbz vbd vbp vb md vp sq')],
    'ucp' : [('right-to-left', '')],
    'vp' : [('left-to-right', 'to vbd vbn md vbz vb vbg vbp vp adjp nn nns np')],
    'whadjp' : [('left-to-right', 'cc wrb jj adjp')],
    'whadvp' : [('right-to-left', 'cc wrb')],
    'whnp' : [('left-to-right', 'wdt wp wp$ whadjp whpp whnp')],
    'whpp' : [('right-to-left', 'in to fw')]
}

# Head rules for NeGra/TIGER from rparse
# almost identical to corresponding rules from Stanford parser
HEAD_RULES_NEGRA = {
    's' : [('right-to-left', 'vvfin vvimp'),
           ('right-to-left', 'vp cvp'),
           ('right-to-left', 'vmfin vafin vaimp'),
           ('right-to-left', 's cs')],
    'vp' : [('right-to-left', 'vvinf vvizu vvpp'),
            ('right-to-left', 'vz vainf vminf vmpp vapp pp')],
    'vz' : [('right-to-left', 'vvinf vainf vminf vvfin vvizu'),
            ('left-to-right', 'prtzu appr ptkzu')],
    'np' : [('right-to-left', 'nn ne mpn np cnp pn car')],
    'ap' : [('right-to-left', 'adjd adja cap aa adv')],
    'pp' : [('left-to-right', 'kokom appr proav')],
    'co' : [('left-to-right', '')],
    'avp' : [('right-to-left', 'adv avp adjd proav pp')],
    'aa' : [('right-to-left', 'adjd adja')],
    'cnp' : [('right-to-left', 'nn ne mpn np cnp pn car')],
    'cap' : [('right-to-left', 'adjd adja cap aa adv')],
    'cpp' : [('right-to-left', 'appr proav pp cpp')],
    'cs' : [('right-to-left', 's cs')],
    'cvp' : [('right-to-left', 'vz')],
    'cvz' : [('right-to-left', 'vz')],
    'cavp' : [('right-to-left', 'adv avp adjd pwav appr ptkvz')],
    'mpn' : [('right-to-left', 'ne fm card')],
    'nm' : [('right-to-left', 'card nn')],
    'cac' : [('right-to-left', 'appr avp')],
    'ch' : [('right-to-left', '')],
    'mta' : [('right-to-left', 'adja adjd nn')],
    'ccp' : [('right-to-left', 'avp')],
    'dl' : [('left-to-right', '')],
    'isu' : [('right-to-left', '')],
    'ql' : [('right-to-left', '')],
    '-' : [('right-to-left', 'pp')],
    'cd' : [('right-to-left', 'cd')],
    'nn' : [('right-to-left', 'nn')],
    'nr' : [('right-to-left', 'nr')],
    'vroot' : [('left-to-right', '$. $')]
}

def get_headpos_by_rule(parent_label, children_label, rules, 
                        default=0):
    """Given parent and children labels and head rules,
    return position of lexical head.
    """
    if not parent_label.lower() in rules:
        return default
    for hrule in rules[parent_label.lower()]:
        if len(hrule[1]) == 0:
            if hrule[0] == 'left-to-right':
                return len(children_label) - 1
            elif hrule[0] == 'right-to_left':
                return 0
            else:
                raise ValueError("unknown head rule direction")
        for label in hrule[1]:
            if hrule[0] == 'left-to-right':
                for i, child_label in enumerate(children_label):
                    parsed_label = trees.parse_label(child_label.lower())
                    if parsed_label.label.lower() == label:
                        return i
            elif hrule[0] == 'right-to-left':
                for i, child_label in \
                    itertools.izip(reversed(xrange(len(children_label))),
                                   reversed(children_label)):
                    parsed_label = trees.parse_label(child_label.lower())
                    if parsed_label.label.lower() == label:
                        return i
                return 0
            else:
                raise ValueError("unknown head rule direction")
    return 0
