"""
treetools: Tools for transforming treebank trees.

This module handles reading of trees. Tree readers are implemented
as generators reading from a file with a given encoding and yielding
trees.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import with_statement, print_function
import io
import re
import string
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
from . import trees, misc
# In Python 3.5, unicode() does not exist anymore, just str()
try:
    type(unicode)
except NameError:
    unicode = lambda s: str(s)


def tigerxml_build_tree(s_element, **params):
    """Build a tree from a <s> element in TIGER XML. If there is
    no unique VROOT, add one (unary). Root is found by looking for
    nodes with no parent, 'root' attribute on <graph> is discarded.
    """
    gf_separator = trees.DEFAULT_GF_SEPARATOR
    if 'gf_separator' in params:
        gf_separator = params['gf_separator']
    idref_to_tree = dict()
    # handle terminals
    term_cnt = 1
    for node in s_element.find('graph').find('terminals').findall('t'):
        subtree = trees.Tree(trees.make_node_data())
        subtree.data['word'] = unicode(node.get('word'))
        subtree.data['label'] = node.get('pos')
        subtree.data['morph'] = node.get('morph')
        subtree.data['lemma'] = node.get('lemma')
        subtree.data['edge'] = trees.DEFAULT_EDGE
        subtree.data['num'] = term_cnt
        term_cnt += 1
        idref_to_tree[node.get('id')] = subtree
    # handle non-terminals
    for node in s_element.find('graph').find('nonterminals').findall('nt'):
        subtree = trees.Tree(trees.make_node_data())
        subtree.data['label'] = node.get('cat')
        subtree.data['morph'] = trees.DEFAULT_MORPH
        subtree.data['edge'] = trees.DEFAULT_EDGE
        subtree.data['lemma'] = trees.DEFAULT_LEMMA
        idref_to_tree[node.get('id')] = subtree
    # set edge labels and link the tree
    for node in s_element.find('graph').find('nonterminals').findall('nt'):
        subtree = idref_to_tree[node.get('id')]
        for edge in node.findall('edge'):
            child = idref_to_tree[edge.get('idref')]
            child.data['edge'] = edge.get('label')
            if child.parent is not None:
                raise ValueError("more than one incoming edge for one node")
            child.parent = subtree
            subtree.children.append(child)
    root = None
    roots = []
    for subtree in idref_to_tree.values():
        if subtree.parent is None:
            roots.append(subtree)
    if len(roots) == 0:
        raise ValueError("looks like a cycle")
    if len(roots) > 1:
        raise ValueError("multiple roots: %s" % " ".join([node.data['label'] 
                                                          for node in roots]))
    root = roots[0]
    top = root
    if not root.data['label'] == trees.DEFAULT_ROOT:
        top = trees.Tree(trees.make_node_data())
        top.data['label'] = trees.DEFAULT_ROOT
        top.children.append(root)
        top.data['morph'] = trees.DEFAULT_MORPH
        top.data['edge'] = trees.DEFAULT_EDGE
        top.data['lemma'] = trees.DEFAULT_LEMMA
        root.parent = top
    # split gf as postprocessing step if applicable
    if 'gf_split' in params:
        coindexseparator = trees.DEFAULT_COINDEX_SEPARATOR
        if len(label_parts.coindex) == 0:
            coindexseparator = trees.DEFAULT_COINDEX_SEPARATOR
        gapseparator = trees.DEFAULT_GAPPING_SEPARATOR
        if len(label_parts.gapindex) == 0:
            gapseparator = ""
        for subtree in trees.preorder(top):
            label_parts = trees.parse_label(subtree.data['label'], \
                                      gf_separator=gf_separator)
            subtree.data['label'] = label_parts.label \
                                    + gapseparator\
                                    + label_parts.gapindex \
                                    + coindexseparator\
                                    + label_parts.coindex \
                                    + label_parts.headmarker
            subtree.data['edge'] = label_parts.gf
    return top


def tigerxml(in_file, _, **params):
    """Read trees from TIGER XML. The encoding argument is ignored here.
    """
    digits = re.compile(r'\d+')
    with io.open(in_file, mode='rb') as stream:
        if not 'quiet' in params:
            print("parsing xml...", file=sys.stderr)
        corpus = ET.parse(stream)
        tree_cnt = 0
        if not 'quiet' in params:
            print("reading sentences", file=sys.stderr)
        for s_element in corpus.getroot().find('body').findall('s'):
            tree_cnt += 1
            # take last number (assume there always is one)
            xml_id = s_element.get('id')
            xml_id = digits.findall(xml_id)[-1]
            tree_id = tree_cnt if 'continuous' in params \
                else int(xml_id)
            try:
                tree = tigerxml_build_tree(s_element, **params)
                tree.data['sid'] = tree_id
                if 'replace_parens' in params:
                    for subtree in trees.preorder(tree):
                        subtree = trees.replace_chars(subtree, trees.BRACKETS)
                yield tree
            except ValueError as error:
                if not 'quiet' in params:
                    print("\nskipping sentence %d: %s\n" % (tree_id, error),
                          file=sys.stderr)


def bracket_lexer(stream):
    """Lexes input coming from stream in opening and closing brackets,
    whitespace, and remaining characters. Works as generator."""
    tokenbuf = StringIO()
    whitespacebuf = StringIO()
    character = stream.read(1)
    while not character == "":
        # holds tokens
        tval = tokenbuf.getvalue()
        # holds whitespace
        wval = whitespacebuf.getvalue()
        if len(tval) > 0 and len(wval) > 0:
            raise ValueError("something went wrong in the lexer")
        if character in trees.PHRASE_BRACKETS:
            if len(tval) > 0:
                yield tval, "TOKEN"
                tokenbuf.close()
                tokenbuf = StringIO()
            if len(wval) > 0:
                yield wval, "WS"
                whitespacebuf.close()
                whitespacebuf = StringIO()
            yield character, trees.BRACKETS[character]
        elif character in string.whitespace:
            if len(tval) > 0:
                yield tval, "TOKEN"
                tokenbuf.close()
                tokenbuf = StringIO()
            whitespacebuf.write(character)
        else:
            if len(wval) > 0:
                yield wval, "WS"
                whitespacebuf.close()
                whitespacebuf = StringIO()
            tokenbuf.write(character)
        character = stream.read(1)


def brackets(in_file, in_encoding, **params):
    """Read bracketed trees with any kind of indentation by lexing
    input into whitespace, left/right brackets, and other tokens (aka
    labels/words).
    States:
       0   expect sentence
       1   expect whitespace or label (phrase label)
       2   expect whitespace or left bracket (next child)
       3   expect whitespace, word or left bracket (word or next child)
       4   expect whitespace or right bracket (end of phrase after word)
       5   expect whitespace or left bracket or right bracket
           (next child or parent)
       9   expect possibly empty label (root label)
    """
    in_file = misc.gunzip(in_file)
    gf_separator = trees.DEFAULT_GF_SEPARATOR
    if 'gf_separator' in params:
        gf_separator = params['gf_separator']
    cnt = 1
    if 'brackets_firstid' in params:
        cnt = params['brackets_firstid']
    if not 'quiet' in params:
        print("first sentence id will be %d" % cnt)
    queue = []
    state = 0
    level = 0
    term_cnt = 1
    with io.open(in_file, encoding=in_encoding) as stream:
        lexer = bracket_lexer(stream)
        for lextoken, lexclass in lexer:
            if lexclass == "LRB":
                if state in [0, 2, 3, 5]:
                    # beginning of sentence or phrase
                    level += 1
                    queue.append(trees.Tree(trees.make_node_data()))
                    state = 9 if state == 0 else 1
                elif state == 9:
                    # happens when root label is empty (PTB style)
                    level += 1
                    queue[-1].data['label'] = trees.DEFAULT_ROOT
                    queue.append(trees.Tree(trees.make_node_data()))
                    state = 1
                elif state == 1:
                    raise ValueError("expected whitespace or label, got (")
                elif state == 4:
                    raise ValueError("expected whitespace or ), got (")
                else:
                    raise ValueError("unknown state")
            elif lexclass == "RRB":
                if state in [0]:
                    pass
                elif state in [2, 4, 5]:
                    if state == 2:
                        if not 'brackets_emptypos' in params:
                            raise ValueError("expected whitespace or (, got )")
                        else:
                            if not 'quiet' in params:
                                print("got empty POS", file=sys.stderr)
                            # last token was a word
                            queue[-1].data['word'] = queue[-1].data['label']
                            # queue[-1].data['label'] = queue[-2].data['label']
                            queue[-1].data['label'] = trees.DEFAULT_LABEL
                            queue[-1].data['edge'] = trees.DEFAULT_EDGE
                            queue[-1].data['morph'] = trees.DEFAULT_MORPH
                            queue[-1].data['num'] = term_cnt
                            term_cnt += 1
                    level -= 1
                    if len(queue) > 1:
                        # close phrase
                        queue[-2].children.append(queue[-1])
                        queue[-1].parent = queue[-2]
                        queue.pop()
                    if level == 0:
                        # close sentence
                        queue[0].data['sid'] = cnt
                        cnt += 1
                        if 'replace_parens' in params:
                            for subtree in trees.preorder(queue[0]):
                                subtree = trees.replace_chars(subtree,
                                                              trees.BRACKETS)
                        if 'disco' in params and params['disco']:
                            terminalmap = {}
                            for terminal in trees.terminals(queue[0]):
                                terminalmap[int(terminal.data['word'])] = terminal
                            tokenmap = defaultdict(int)
                            position = 1
                            try:
                                lextoken, lexclass = lexer.next()
                            except StopIteration:
                                raise ValueError("no sentence after tree")
                            try:
                                while not lextoken == "\n":
                                    lextoken, lexclass = lexer.next()
                                    if not lextoken == ' ':
                                        tokenmap[position] = lextoken
                                        position += 1
                            except StopIteration:
                                pass
                            if 'disco_reordered' in params:
                                for terminal in trees.terminals(queue[0]):
                                    terminal.data['word'] = terminal.data['word'] + "-" \
                                        + tokenmap[terminal.data['num']]
                            else:
                                for terminal in trees.terminals(queue[0]):
                                    terminal.data['num'] = int(terminal.data['word']) + 1
                                    terminal.data['word'] = tokenmap[terminal.data['num']]
                        yield queue[0]
                        term_cnt = 1
                        queue = []
                        state = 0
                    else:
                        state = 5
                elif state == 1:
                    raise ValueError("expected label, got )")
                elif state in [3, 9]:
                    raise ValueError("expected whitespace, label or (, got )")
                else:
                    raise ValueError("unknown state")
            elif lexclass == "WS":
                if state in [0, 1, 3, 4, 5, 9]:
                    pass
                elif state == 2:
                    # only don't skip whitespace if it's then one between POS
                    # and word
                    state = 3
                else:
                    raise ValueError("unknown state")
            elif lexclass == "TOKEN":
                if state == 0:
                    pass
                elif state in [1, 9]:
                    # phrase label, 9 when root label, 1 otherwise
                    if 'gf_split' in params:
                        label_parts = trees.parse_label(lextoken,
                                                  gf_separator=gf_separator)
                        separator = gf_separator
                        if len(label_parts.coindex) == 0:
                            separator = ""
                        gapseparator = trees.DEFAULT_GAPPING_SEPARATOR
                        if len(label_parts.gapindex) == 0:
                            gapseparator = ""
                        label = label_parts.label \
                                + gapseparator \
                                + label_parts.gapindex \
                                + separator \
                                + label_parts.coindex \
                                + label_parts.headmarker
                        edge = label_parts.gf
                    else:
                        label = lextoken
                        edge = trees.DEFAULT_EDGE
                    queue[-1].data['label'] = label
                    queue[-1].data['edge'] = edge
                    queue[-1].data['morph'] = trees.DEFAULT_MORPH
                    state = 2
                elif state == 3:
                    queue[-1].data['word'] = lextoken
                    queue[-1].data['num'] = term_cnt
                    term_cnt += 1
                    state = 4
                elif state == 2:
                    raise ValueError("expected whitespace or (, got token")
                elif state == 4:
                    raise ValueError("expected whitespace or ), got token")
                elif state == 5:
                    raise ValueError("expected whitespace, ( or ), got token")
                else:
                    raise ValueError("unknown state")
            else:
                raise ValueError("unknown lexer token class")


def discobrackets(in_file, in_encoding, **params):
    """ Build a tree from disco bracket input. Every terminal is supposed to
    be an integer i. For a sentence of length n, all 1 <= i <= n must be
    present. Tree is parsed as regular bracketed tree; after that, the 
    terminals are reordered w.r.t. to their numbering. 

    The required format is one tree per line, after each tree a tab is 
    expected, followed by the tokens in their correct order, separated by
    a space.
    """
    params['disco'] = True
    for tree in brackets(in_file, in_encoding, **params):
        yield tree


def export_build_tree(num, node_by_num, children_by_num):
    """ Build a tree from export. """
    tree = trees.Tree(node_by_num[num])
    tree.data['terminals'] = []
    if num in children_by_num:
        tree.children = []
        for child in children_by_num[num]:
            child_tree = export_build_tree(child, node_by_num, children_by_num)
            child_tree.parent = tree
            tree.children.append(child_tree)
            tree.data['terminals'].extend(child_tree.data['terminals'])
        tree.children = sorted(tree.children, \
                                    key=lambda x: min(x.data['terminals']))
    else:
        tree.children = []
        tree.data['terminals'] = [num]
        tree.data['num'] = num
    tree.data['terminals'] = sorted(tree.data['terminals'])
    return tree


def export_parse_line(line, **params):
    """ Parse a single export format line, i.e., one node."""
    gf_separator = trees.DEFAULT_GF_SEPARATOR
    if 'gf_separator' in params:
        gf_separator = params['gf_separator']
    fields = line.split()
    # if it is export 3, insert dummy lemma
    if fields[4].isdigit():
        fields[1:1] = [trees.DEFAULT_LEMMA]
    if len(fields) < trees.NUMBER_OF_FIELDS:
        raise ValueError("too few fields")
    # throw away after parent number and assign to fields
    fields = dict(zip(trees.FIELDS, fields[:trees.NUMBER_OF_FIELDS]))
    fields['parent_num'] = int(fields['parent_num'])
    if not (500 <= fields['parent_num'] < 1000 or fields['parent_num'] == 0):
        raise ValueError("parent field must be 0 or between 500 and 999")
    # options?
    if 'gf_split' in params:
        label_parts = trees.parse_label(fields['label'],
                                        gf_separator=gf_separator)
        separator = gf_separator
        if len(label_parts.coindex) == 0:
            separator = ""
        gapseparator = trees.DEFAULT_GAPPING_SEPARATOR
        if len(label_parts.gapindex) == 0:
            gapseparator = ""
        fields['label'] = label_parts.label \
                          + gapseparator\
                          + label_parts.gapindex\
                          + separator\
                          + label_parts.coindex\
                          + label_parts.headmarker
        fields['edge'] = label_parts.gf
    return fields


def export(in_file, in_encoding, **params):
    """Read export format (3 or 4). Ignores all fields after the parent number
    since not all export treebanks respect the original export definition
    from Brants (1997) (see TueBa-D/Z 8).
    """
    in_file = misc.gunzip(in_file)
    in_sentence = False
    sentence = []
    last_id = None
    tree_cnt = 1
    with io.open(in_file, encoding=in_encoding) as stream:
        for line in stream:
            line = line.strip()
            if not in_sentence:
                if line.startswith(u"#BOS"):
                    last_id = int(line.split()[1])
                    in_sentence = True
                    sentence.append(line)
            else:
                sentence.append(line)
                if line.startswith(u"#EOS"):
                    node_by_num = {}
                    children_by_num = {}
                    node_by_num[0] = trees.make_node_data()
                    node_by_num[0]['label'] = trees.DEFAULT_ROOT
                    node_by_num[0]['edge'] = trees.DEFAULT_EDGE
                    term_cnt = 1
                    for fields in [export_parse_line(line, **params) \
                                       for line in sentence[1:-1]]:
                        word = fields['word']
                        num = None
                        if len(word) == 4 and word[0] == u"#" \
                                and word[1:].isdigit():
                            num = int(word[1:])
                        else:
                            num = term_cnt
                            term_cnt += 1
                        if not 0 <= num <= 999:
                            raise ValueError("node number must 0 and 999")
                        node_by_num[num] = fields
                        if not fields['parent_num'] in children_by_num:
                            children_by_num[fields['parent_num']] = []
                        children_by_num[fields['parent_num']].append(num)
                    tree = export_build_tree(0, node_by_num, children_by_num)
                    tree.data['sid'] = tree_cnt if 'continuous' in params \
                        else last_id
                    if 'replace_parens' in params:
                        for subtree in trees.preorder(tree):
                            subtree = trees.replace_chars(subtree,
                                                          trees.BRACKETS)
                    yield tree
                    term_cnt = 1
                    tree_cnt += 1
                    in_sentence = False
                    sentence = []


INPUT_FORMATS = [export, brackets, discobrackets, tigerxml]
INPUT_OPTIONS = {'disco_reordered' : 'In discobrackets, output CF order with '\
                     'terminal indices',
                 'gf_split' : 'Brackets: Try to split grammatical ' \
                     'functions from label at last occurrence of gf separator',
                 'gf_separator' : 'Brackets: Separator to use for ' \
                     ' gf option (default %s)' % trees.DEFAULT_GF_SEPARATOR,
                 'brackets_emptypos' : 'Brackets: Allow empty POS tags',
                 'brackets_firstid' : 'Brackets: Give first tree id [ID]',
                 'continuous' : 'Export/TIGERXML: number sentences by ' \
                     'counting, don\'t use #BOS',
                 'replace_parens' : 'Replace parens by LRB, RRB, etc. ',
                 'quiet' : 'no messages while reading'}
