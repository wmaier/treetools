""" 
treetools: Tools for transforming treebank trees.

This module handles reading of trees. Tree readers are implemented 
as generators reading from a file with a given encoding and yielding 
trees. 

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import with_statement
import io
from StringIO import StringIO
from . import trees 


CHARACTERS = { "(" : "LRB", ")" : "RRB",
               " " : "WS", "\t" : "WS", "\n" : "WS", 
               "\r" : "WS", "\f" : "WS", "\v" : "WS" }


def bracket_lexer(stream):
    """Lexes input coming from stream in opening and closing brackets, 
    whitespace, and remaining characters. Works as generator."""
    buf = StringIO()
    character = stream.read(1)
    while not character == "":
        if character in CHARACTERS:
            if len(buf.getvalue()) > 0:
                yield buf.getvalue(), "TOKEN"
                buf.close()
                buf = StringIO()
            yield character, CHARACTERS[character]
        else:
            buf.write(character)
        character = stream.read(1)


def brackets(in_file, in_encoding, **params):
    """Read bracketed trees with any kind of indentation by lexing
    input into whitespace, left/right brackets, and other tokens (aka 
    labels/words). 
    States:
       0   expect sentence
       1   expect whitespace or label
       2   expect whitespace or left bracket
       3   expect whitespace, word or left bracket
       4   expect whitespace or right bracket
       5   expect whitespace or left bracket or right bracket
    """
    queue = []
    state = 0
    level = 0
    with io.open(in_file, encoding=in_encoding) as stream:
        for lextoken, lexclass in bracket_lexer(stream):
            if lexclass == "LRB":
                if state in [0, 2, 3, 5]:
                    level += 1
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
                    state = 5 if not level == 0 else 0
                elif state == 1:
                    raise ValueError("expected label, got )")
                elif state == 2:
                    raise ValueError("expected whitespace or (, got )")
                elif state == 3:
                    raise ValueError("expected whitespace, label or (, got )")
                else:
                    raise ValueError("unknown state")
            elif lexclass == "WS":
                if state in [0, 1, 3, 4, 5]:
                    pass
                elif state == 2:
                    state = 3
                else:
                    raise ValueError("unknown state")
            elif lexclass == "TOKEN":
                if state in [0]:
                    pass
                elif state == 1:
                    state = 2
                elif state == 3:
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
            print lextoken, "\t", lexclass, "\t", state


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


def export_parse_line(line):
    """ Parse a single export format line, i.e., one node."""
    fields = line.split()
    # if it is export 3, insert dummy lemma
    if fields[4].isdigit():
        fields[1:1] = [u"--"]
    if len(fields) < trees.NUMBER_OF_FIELDS:
        raise ValueError("too few fields")
    # throw away after parent number and assign to fields
    fields = dict(zip(trees.FIELDS, fields[:trees.NUMBER_OF_FIELDS])) 
    fields['parent_num'] = int(fields['parent_num'])
    if not (500 <= fields['parent_num'] < 1000 or fields['parent_num'] == 0):
        raise ValueError("parent field must be 0 or between 500 and 999")
    # replace stuff TODO: make this nicer
    equals_pos = fields['label'].find("=")
    if equals_pos >= 0:
        fields['label'] = fields['label'][0:equals_pos]
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
                    node_by_num[0]['edge'] = u"--"
                    term_cnt = 1
                    for fields in [export_parse_line(line) \
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
                    tree['id'] = tree_cnt if 'export_continuous' in params \
                                 else last_id
                    yield tree
                    tree_cnt += 1
                    in_sentence = False
                    sentence = []

INPUT_FORMATS = [export, brackets]
INPUT_OPTIONS = { 'export_continuous' : 
                  'Export: number sentences by counting, don\'t use #BOS' }
