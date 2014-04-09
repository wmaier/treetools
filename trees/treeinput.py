""" 
treetools: Tools for transforming treebank trees.

This module handles reading of trees. Tree readers are implemented 
as generators reading from a file with a given encoding and yielding 
trees. 

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import with_statement, print_function
import io
import string
import sys
import xml.etree.ElementTree as ET
from StringIO import StringIO
from . import trees 


BRACKETS = { "(" : "LRB", ")" : "RRB" }


def tigerxml_build_tree(s):
    """Build a tree from a <s> element in TIGER XML. If there is 
    no unique VROOT, add one. So far, head marking in the XML
    is discarded.
    """
    idref_to_tree = dict()
    # handle terminals
    term_cnt = 1
    for node in s.find('graph').find('terminals').findall('t'):
        subtree = trees.make_tree(trees.make_node_data())
        subtree['word'] = node.get('word')
        subtree['label'] = node.get('pos')
        subtree['morph'] = node.get('morph')
        subtree['lemma'] = node.get('lemma')
        subtree['edge'] = trees.DEFAULT_EDGE
        subtree['num'] = term_cnt
        term_cnt += 1
        idref_to_tree[node.get('id')] = subtree
    # handle non-terminals
    for node in s.find('graph').find('nonterminals').findall('nt'):
        subtree = trees.make_tree(trees.make_node_data())
        subtree['label'] = node.get('cat')
        subtree['morph'] = trees.DEFAULT_MORPH
        subtree['edge'] = trees.DEFAULT_EDGE
        subtree['lemma'] = trees.DEFAULT_LEMMA
        idref_to_tree[node.get('id')] = subtree
    # set edge labels and link the tree
    for node in s.find('graph').find('nonterminals').findall('nt'):
        subtree = idref_to_tree[node.get('id')]
        for edge in node.findall('edge'):
            child = idref_to_tree[edge.get('idref')]
            child['edge'] = edge.get('label')
            if child['parent'] is not None:
                raise ValueError("more than one incoming edge")
            child['parent'] = subtree
            subtree['children'].append(child)
    root = None
    for subtree in idref_to_tree.values():
        if subtree['parent'] is None:
            if root is None:
                root = subtree 
            else:
                raise ValueError("more than one root node")
    top = root
    if not root['label'] == "VROOT":
        top = trees.make_tree(trees.make_node_data())
        top['label'] = u"VROOT"
        top['children'].append(root)
        top['morph'] = trees.DEFAULT_MORPH
        top['edge'] = trees.DEFAULT_EDGE
        top['lemma'] = trees.DEFAULT_LEMMA
        root['parent'] = top
    return top


def tigerxml(in_file, in_encoding, **params):
    """Read trees from TIGER XML.  
    """
    with open(in_file, encoding=in_encoding) as stream:
        print("parsing xml...", file=sys.stderr)
        corpus = ET.parse(stream)
        tree_cnt = 0
        print("reading sentences...", file=sys.stderr)
        for s in corpus.getroot().find('body').findall('s'):
            tree_cnt += 1;
            try:
                tree = tigerxml_build_tree(s)
                tree['id'] = tree_cnt if 'continuous' in params \
                    else int(s.get('id')[1:])
                yield tree
            except ValueError as e:
                print("\nsentence %d: %s\n" % (tree_cnt, e), file=sys.stderr)


def brackets_split_label(label, gf_separator, trunc_equals):
    """Take a label, try to split it at first occurrence of 
    gf separator, return tuple with label and gf. Numbers at the
    end of the label (with the default separator character "-" 
    prepended) are taken to be co-indexation marks and re-glued 
    to the label, "'" at the end of the label is taken to be 
    head marking and also kept. If no separator present (or only 
    co-indexation), default edge is returned.""" 
    edge = trees.DEFAULT_EDGE
    if trunc_equals:
        equals_pos = label.find("=")
        if equals_pos > -1:
            label = label[:equals_pos]
    headmarker = ""
    if label[-1] == trees.DEFAULT_HEAD_MARKER:
        headmarker = label[-1]
        label = label[:-1]
    coindex = ""
    coindex_sep = label.rfind(trees.DEFAULT_GF_SEPARATOR)
    if coindex_sep > -1:
        if label[coindex_sep + 1:].isdigit():
            coindex = "%s%s" % (trees.DEFAULT_GF_SEPARATOR, 
                                label[coindex_sep + 1:])
            label = label[:coindex_sep]
    sep = label.find(gf_separator)
    if sep > 0:
        edge = label[sep + 1:]
        label = label[:sep]
    return ("%s%s%s" % (label, coindex, headmarker)), edge


def bracket_lexer(stream):
    """Lexes input coming from stream in opening and closing brackets, 
    whitespace, and remaining characters. Works as generator."""
    tokenbuf = StringIO()
    whitespacebuf = StringIO()
    character = stream.read(1)
    while not character == "":
        tval = tokenbuf.getvalue()
        wval = whitespacebuf.getvalue()
        if len(tval) > 0 and len(wval) > 0:
            raise ValueError("something went wrong in the lexer")
        if character in BRACKETS:
            if len(tval) > 0:
                yield tval, "TOKEN"
                tokenbuf.close()
                tokenbuf = StringIO()
            if len(wval) > 0:
                yield wval, "WS"
                whitespacebuf.close()
                whitespacebuf = StringIO()
            yield character, BRACKETS[character]
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
    split_gf = 'brackets_gf' in params
    gf_separator = trees.DEFAULT_GF_SEPARATOR
    if 'brackets_gf_separator' in params:
        gf_separator = params['brackets_gf_separator']
    trunc_equals = 'trunc_equals' in params
    queue = []
    state = 0
    level = 0
    term_cnt = 1
    cnt = 1
    with io.open(in_file, encoding=in_encoding) as stream:
        for lextoken, lexclass in bracket_lexer(stream):
            if lexclass == "LRB":
                if state in [0, 2, 3, 5]:
                    # beginning of sentence or phrase
                    level += 1
                    queue.append(trees.make_tree(trees.make_node_data()))
                    state = 9 if state == 0 else 1
                elif state == 9:
                    # happens when root label is empty (PTB style)
                    level += 1
                    queue[-1]['label'] = u"VROOT"
                    queue.append(trees.make_tree(trees.make_node_data()))
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
                elif state in [4, 5]:
                    level -= 1
                    if len(queue) > 1:
                        # close phrase
                        queue[-2]['children'].append(queue[-1])
                        queue[-1]['parent'] = queue[-2]
                        queue.pop()
                    if level == 0:
                        # close sentence
                        queue[0]['id'] = cnt
                        cnt += 1
                        yield queue[0]
                        queue = []
                        state = 0
                    else:
                        state = 5
                elif state == 1:
                    raise ValueError("expected label, got )")
                elif state == 2:
                    raise ValueError("expected whitespace or (, got )")
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
                    if split_gf:
                        label, edge = brackets_split_label(lextoken, 
                                                           gf_separator,
                                                           trunc_equals) 
                    else: 
                        label = lextoken
                        edge = trees.DEFAULT_EDGE
                    queue[-1]['label'] = label
                    queue[-1]['edge'] = edge
                    queue[-1]['morph'] = trees.DEFAULT_MORPH
                    state = 2
                elif state == 3:
                    queue[-1]['word'] = lextoken
                    queue[-1]['num'] = term_cnt 
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


def export_build_tree(num, node_by_num, children_by_num):
    """ Build a tree from export. """
    tree = trees.make_tree(node_by_num[num])
    tree['terminals'] = []
    if num in children_by_num:
        tree['children'] = []
        for child in children_by_num[num]:
            child_tree = export_build_tree(child, node_by_num, children_by_num)
            child_tree['parent'] = tree
            tree['children'].append(child_tree)
            tree['terminals'].extend(child_tree['terminals'])
        tree['children'] = sorted(tree['children'], \
                                    key=lambda x: min(x['terminals']))
    else:
        tree['children'] = []
        tree['terminals'] = [num]
        tree['num'] = num
    tree['terminals'] = sorted(tree['terminals'])
    return tree


def export_parse_line(line, **params):
    """ Parse a single export format line, i.e., one node."""
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
    if 'trunc_equals' in params:
        equals_pos = line.find("=")
        if equals_pos > -1:
            line = line[:equals_pos]
    return fields


def export(in_file, in_encoding, **params):
    """Read export format (3 or 4). Ignores all fields after the parent number 
    since not all export treebanks respect the original export definition
    from Brants (1997) (see TueBa-D/Z 8). 
    """
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
                    node_by_num[0]['label'] = u"VROOT"
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
                    tree['id'] = tree_cnt if 'continuous' in params \
                                 else last_id
                    yield tree
                    tree_cnt += 1
                    in_sentence = False
                    sentence = []

INPUT_FORMATS = [export, brackets, tigerxml]
INPUT_OPTIONS = { 'brackets_gf' : 'Brackets: Try to split grammatical ' \
                  'functions from label at last occurrence of gf separator',
                  'brackets_gf_separator' : 'Brackets: Separator to use for ' \
                  ' gf option (default %s)' % trees.DEFAULT_GF_SEPARATOR,
                  'continuous' : 'Export/TIGERXML: number sentences by ' \
                  'counting, don\'t use #BOS', 
                  'trunc_equals' : 'trucate label at first "=" sign'}
