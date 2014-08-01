"""
treetools: Tools for transforming treebank trees.

Unit tests constants

Author: Wolfgang Maier <maierw@hhu.de>
"""

SAMPLE_BRACKETS = """
((S(WP Who)(VB did)(NNP Fritz)(VP(VB tell)(NNP Hans)(SBAR(IN that)
(NP(NNP Manfred))(VP(VB likes)))))(? ?))
"""
SAMPLE_BRACKETS_TOL = """
((S(Who)(did)(Fritz)(VP(tell)(Hans)(SBAR(that)(NP(Manfred))(VP(likes)
))))(?))
"""
SAMPLE_TIGERXML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<corpus>
<body>
<s id="1">
<graph root="0">
  <terminals>
    <t id="1" word="Who" lemma="--" pos="WP" morph="--" />
    <t id="2" word="did" lemma="--" pos="VB" morph="--" />
    <t id="3" word="Fritz" lemma="--" pos="NNP" morph="--" />
    <t id="4" word="tell" lemma="--" pos="VB" morph="--" />
    <t id="5" word="Hans" lemma="--" pos="NNP" morph="--" />
    <t id="6" word="that" lemma="--" pos="IN" morph="--" />
    <t id="7" word="Manfred" lemma="--" pos="NNP" morph="--" />
    <t id="8" word="likes" lemma="--" pos="VB" morph="--" />
    <t id="9" word="?" lemma="--" pos="?" morph="--" />
  </terminals>
  <nonterminals>
    <nt id="500" cat="VP">
      <edge label="--" idref="1" />
      <edge label="HD" idref="8" />
    </nt>
    <nt id="501" cat="NP">
      <edge label="HD" idref="7" />
    </nt>
    <nt id="502" cat="SBAR">
      <edge label="--" idref="500" />
      <edge label="HD" idref="6" />
      <edge label="--" idref="501" />
    </nt>
    <nt id="503" cat="VP">
      <edge label="--" idref="502" />
      <edge label="HD" idref="4" />
      <edge label="--" idref="5" />
    </nt>
    <nt id="504" cat="S">
      <edge label="--" idref="503" />
      <edge label="HD" idref="2" />
      <edge label="HD" idref="3" />
    </nt>
    <nt id="0" cat="VROOT">
      <edge label="--" idref="504" />
      <edge label="--" idref="9" />
    </nt>
  </nonterminals>
</graph>
</s>
</body>
</corpus>
"""
SAMPLE_EXPORT = """#BOS 1
Who                     WP      --              --      500
did                     VB      --              HD      504
Fritz                   NNP     --              HD      504
tell                    VB      --              HD      503
Hans                    NNP     --              --      503
that                    IN      --              HD      502
Manfred                 NNP     --              HD      501
likes                   VB      --              HD      500
?                       ?       --              --      0
#500                    VP      --              --      502
#501                    NP      --              --      502
#502                    SBAR    --              --      503
#503                    VP      --              --      504
#504                    S       --              --      0
#EOS 1
"""
WORDS = [u'Who', u'did', u'Fritz', u'tell', u'Hans', u'that', u'Manfred', 
         u'likes', u'?']
POS = [u'WP', u'VB', u'NNP', u'VB', u'NNP', u'IN', u'NNP', u'VB', u'?']
DISCONT_EXPORT_NUMBERING = [0, 504, 503, 502, 500, 1, 8, 6, 501, 7, 4, 5, 2, \
                                3, 9]
DISCONT_LABELS_PREORDER = [u'VROOT', u'S', u'VP', u'SBAR', u'VP', u'WP',
                           u'VB', u'IN', u'NP', u'NNP', u'VB', u'NNP',
                           u'VB', u'NNP', u'?']
DISCONT_HEADS_PREORDER = []
DISCONT_RIGHTSIB_PREORDER = [None, u'?', u'VB', u'VB', u'IN', u'VB', 
                             None, u'NP', None, None, u'NNP', None, 
                             u'NNP', None, None]
DISCONT_LEFTSIB_PREORDER = [None, u'?', u'NNP', u'NNP', u'NP', u'VB', 
                            None, u'VP', None, None, u'SBAR', None, 
                            u'VP', None, None]
DISCONT_LABELSBOYD_PREORDER = [u'VROOT', u'S', u'VP', u'SBAR', u'VP',
                               u'WP', u'VB', u'NNP', u'VP', u'VB',
                               u'NNP', u'SBAR', u'IN', u'NP', u'NNP',
                               u'VP', u'VB', u'?']
CONT_LABELS_PREORDER = [u'VROOT', u'S', u'WP', u'VB', u'NNP',
                        u'VP', u'VB', u'NNP', u'SBAR', u'IN',
                        u'NP', u'NNP', u'VP', u'VB', u'?']
CONT_RIGHTSIB_PREORDER = [None, u'?', u'VB', u'NNP', u'VP', 
                          None, u'NNP', u'SBAR', None, u'NP', 
                          u'VP', None, None, None, None]
CONT_LEFTSIB_PREORDER = [None, u'?', u'VP', u'WP', u'VB', None, 
                         u'SBAR', u'VB', None, u'VP', u'IN', None, 
                         None, None, None]
DISCONT_BLOCKS_VP = [[1], [4,5,6,7,8]]
CONT_BLOCKS_VP = [[4,5,6,7,8]]
DISCONT_DOM_FIRST = [u'WP', u'VP', u'SBAR', u'VP',  u'S', u'VROOT']
CONT_DOM_FIRST = [u'WP', u'S', u'VROOT']
# grammar stuff
CONT_GRAMMAR_FUNCS = [(u'VROOT', u'S', u'?'),
                      (u'S', u'WP', u'VB', u'NNP', u'VP'),
                      (u'VP', u'VB', u'NNP', u'SBAR'),
                      (u'SBAR', u'IN', u'NP', u'VP'),
                      (u'NP', u'NNP'),
                      (u'VP', u'VB')]
DISCONT_GRAMMAR_FUNCS = [(u'VROOT', u'S', u'?'), 
                         (u'S', u'VP', u'VB', u'NNP'), 
                         (u'SBAR', u'VP', u'IN', u'NP'), 
                         (u'VP', u'SBAR', u'VB', u'NNP'), 
                         (u'VP', u'WP', u'VB'), 
                         (u'NP', u'NNP')]
DISCONT_GRAMMAR_LINS = [(((0, 0), (1, 0), (2, 0), (0, 1)),),
                        (((0, 0),), ((1, 0), (2, 0), (0, 1))),
                        (((0, 0),), ((1, 0), (2, 0), (0, 1))),
                        (((0, 0), (1, 0)),),
                        (((0, 0),), ((1, 0),)),
                        (((0, 0),),)]
