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
DISCONT_LEFTSIB_PREORDER = [None, None, None, None, None, None, u'WP', 
                            u'VP', u'IN', None, u'SBAR', u'VB', u'VP', 
                            u'VB', u'S']
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
CONT_LEFTSIB_PREORDER = [None, None, None, u'WP', u'VB', u'NNP', None, 
                         u'VB', u'NNP', None, u'IN', None, u'NP', None, 
                         u'S']
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
CONT_GRAMMAR_LEFT_RIGHT = {('@1X', u'NP', u'VP'): {(((0, 0), (1,
                                                              0)),):
                                                   {'VERT': 1}},
                           (u'S',
                            u'WP',
                            '@3X'): {(((0, 0), (1, 0)),): {'VERT':
                                                           1}},
                           (u'VP', u'VB'): {(((0, 0),),):
                                            {'VERT': 1}}, (u'VP',
                                                           u'VB',
                                                           '@2X'):
                           {(((0, 0), (1, 0)),): {'VERT': 1}}, ('@2X',
                                                                u'NNP',
                                                                u'SBAR'):
                           {(((0, 0), (1, 0)),): {'VERT': 1}},
                           (u'VROOT', u'S', u'?'): {(((0,
                                                       0),
                                                      (1,
                                                       0)),):
                                                    {'VERT':
                                                     1}}, (u'NP',
                                                           u'NNP'):
                           {(((0, 0),),): {'VERT': 1}}, ('@3X', u'VB',
                                                         '@4X'):
                           {(((0, 0), (1, 0)),): {'VERT': 1}}, ('@4X',
                                                                u'NNP',
                                                                u'VP'):
                           {(((0,
                               0),
                              (1,
                               0)),):
                            {'VERT':
                             1}}, (u'SBAR', u'IN', '@1X'): {(((0, 0),
                                                              (1,
                                                               0)),):
                                                            {'VERT':
                                                             1}}} 
DISCONT_GRAMMAR_LEFT_RIGHT = {(u'VP', u'SBAR', '@3X'): \
                              {(((0, 0),), ((1, 0),
                                            (0, 1))):
                               {'VERT': 1}}, ('@1X',
                                              u'VB',
                                              u'NNP'): \
                              {(((0, 0), (1, 0)),): {'VERT': 1}}, (u'S',
                                                                   u'VP',
                                                                   '@1X'):
                              {(((0, 0), (1, 0), (0, 1)),): {'VERT': 1}},
                              ('@3X', u'VB', u'NNP'): {(((0, 0), (1, 0)),):
                                                       {'VERT': 1}},
                              (u'VROOT', u'S', u'?'): {(((0, 0), (1, 0)),):
                                                       {'VERT': 1}}, (u'NP',
                                                                      u'NNP'):
                              {(((0, 0),),): {'VERT': 1}}, (u'VP', u'WP',
                                                            u'VB'): {(((0,
                                                                        0),),
                                                                      ((1,
                                                                        0),)):
                                                                     {'VERT':
                                                                      1}},
                              ('@2X', u'IN', u'NP'): {(((0, 0), (1, 0)),):
                                                      {'VERT': 1}}, (u'SBAR',
                                                                     u'VP',
                                                                     '@2X'):
                              {(((0, 0),), ((1, 0), (0, 1))): {'VERT':
                                                                   1}}} 
DISCONT_GRAMMAR_LR_H1_V2_BTOP_BBOT = \
    {(u'@^S1^VROOT1-VP2X', u'VB', u'NNP'): {(((0, 0), (1, 0)),): {'VERT':
                                                                      1}},
     (u'SBAR', u'VP', u'@^SBAR2^VP2-VP2X'): {(((0, 0),), ((1, 0), (0,
                                                                   1))):
                                                 {'VERT': 1}}, (u'VP',
                                                                u'SBAR',
                                                                u'@^VP2^S1-SBAR2X'):
         {(((0, 0),), ((1, 0), (0, 1))): {'VERT': 1}}, (u'VP', u'WP',
                                                        u'VB'): {(((0,
                                                                    0),),
                                                                  ((1,
                                                                    0),)):
                                                                     {'VERT':
                                                                          1}},
     (u'VROOT', u'S', u'?'): {(((0, 0), (1, 0)),): {'VERT': 1}},
     (u'@^VP2^S1-SBAR2X', u'VB', u'NNP'): {(((0, 0), (1, 0)),): {'VERT':
                                                                     1}},
     (u'S', u'VP', u'@^S1^VROOT1-VP2X'): {(((0, 0), (1, 0), (0, 1)),):
                                              {'VERT': 1}}, (u'NP',
                                                             u'NNP'):
         {(((0, 0),),): {'VERT': 1}}, (u'@^SBAR2^VP2-VP2X', u'IN', u'NP'):
         {(((0, 0), (1, 0)),): {'VERT': 1}}}
DISCONT_GRAMMAR_LR_H2_V1_BTOP_BBOT = \
    {(u'SBAR', u'VP', u'@^SBAR2-VP2X'): {(((0, 0),), ((1, 0), (0, 1))):
                                             {'VERT': 1}}, (u'S', u'VP',
                                                            u'@^S1-VP2X'):
         {(((0, 0), (1, 0), (0, 1)),): {'VERT': 1}}, (u'@^VP2-SBAR2X',
                                                      u'VB', u'NNP'):
         {(((0, 0), (1, 0)),): {'VERT': 1}}, (u'VROOT', u'S', u'?'):
         {(((0, 0), (1, 0)),): {'VERT': 1}}, (u'@^S1-VP2X', u'VB',
                                              u'NNP'): {(((0, 0), (1,
                                                                   0)),):
                                                            {'VERT': 1}},
     (u'VP', u'WP', u'VB'): {(((0, 0),), ((1, 0),)): {'VERT': 1}}, (u'VP',
                                                                    u'SBAR',
                                                                    u'@^VP2-SBAR2X'):
         {(((0, 0),), ((1, 0), (0, 1))): {'VERT': 1}}, (u'@^SBAR2-VP2X',
                                                        u'IN', u'NP'):
         {(((0, 0), (1, 0)),): {'VERT': 1}}, (u'NP', u'NNP'): {(((0,
                                                                  0),),):
                                                                   {'VERT':
                                                                        1}}}

DISCONT_GRAMMAR_OUTPUT_RCG = [
    "C:1 SBAR2([0],[1][2][3]) --> VP2([0],[3]) IN1([1]) NP1([2])",
    "C:1 VP2([0],[1][2][3]) --> SBAR2([0],[3]) VB1([1]) NNP1([2])",
    "C:1 S1([0][1][2][3]) --> VP2([0],[3]) VB1([1]) NNP1([2])",
    "C:1 NP1([0]) --> NNP1([0])",
    "C:1 VP2([0],[1]) --> WP1([0]) VB1([1])",
    "C:1 VROOT1([0][1]) --> S1([0]) ?1([1])"]
CONT_GRAMMAR_OUTPUT_RCG = [
    "C:1 VROOT1([0][1]) --> S1([0]) ?1([1])",
    "C:1 VP1([0]) --> VB1([0])",
    "C:1 S1([0][1][2][3]) --> WP1([0]) VB1([1]) NNP1([2]) VP1([3])",
    "C:1 SBAR1([0][1][2]) --> IN1([0]) NP1([1]) VP1([2])",
    "C:1 NP1([0]) --> NNP1([0])",
    "C:1 VP1([0][1][2]) --> VB1([0]) NNP1([1]) SBAR1([2])"]
GRAMMAR_OUTPUT_RCG_LEX = [
    "Who\tWP 1", "Fritz\tNNP 1", "Manfred\tNNP 1", "?\t? 1",
    "Hans\tNNP 1", "tell\tVB 1", "that\tIN 1", "likes\tVB 1",
    "did\tVB 1"]
DISCONT_GRAMMAR_OUTPUT_PMCFG = [
    "fun1 : S <- VP VB NNP",
    "fun1 = s1",
    "fun1 1",
    "fun2 : SBAR <- VP IN NP",
    "fun2 = s2 s3",
    "fun2 1",
    "fun3 : VP <- SBAR VB NNP",
    "fun3 = s2 s3",
    "fun3 1",
    "fun4 : VROOT <- S ?",
    "fun4 = s4",
    "fun4 1",
    "fun5 : VP <- WP VB",
    "fun5 = s2 s5",
    "fun5 1",
    "fun6 : NP <- NNP",
    "fun6 = s2",
    "fun6 1",
    "s1 -> 0:0 1:0 2:0 0:1",
    "s2 -> 0:0",
    "s3 -> 1:0 2:0 0:1",
    "s4 -> 0:0 1:0",
    "s5 -> 1:0"]
CONT_GRAMMAR_OUTPUT_PMCFG = [
    "fun1 : SBAR <- IN NP VP",
    "fun1 = s1",
    "fun1 1",
    "fun2 : VP <- VB NNP SBAR",
    "fun2 = s1",
    "fun2 1",
    "fun3 : VP <- VB",
    "fun3 = s2",
    "fun3 1",
    "fun4 : S <- WP VB NNP VP",
    "fun4 = s3",
    "fun4 1",
    "fun5 : VROOT <- S ?",
    "fun5 = s4",
    "fun5 1",
    "fun6 : NP <- NNP",
    "fun6 = s2",
    "fun6 1",
    "s1 -> 0:0 1:0 2:0",
    "s2 -> 0:0",
    "s3 -> 0:0 1:0 2:0 3:0",
    "s4 -> 0:0 1:0"]
