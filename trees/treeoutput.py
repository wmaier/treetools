""" 
treetools: Tools for transforming treebank trees.

This module handles tree writing in different formats.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import division
from . import trees, analyze
import sys


DEFAULT_GF_SEPARATOR = u"-"
DEFAULT_HEAD_MARKER = u"'"


def parse_split_specification(split_spec, size):
    """Parse the specification of part sizes for output splitting.
    The specification must be given as list of part size specifications 
    separated by underscores where each part size specification is either a
    number suffixed by '#' (denoting an absolute size) or '%%' (denoting
    a percentage), or the keyword 'rest' which may occur once (denoting
    the part which receives the difference between the given number of
    trees and the sum of trees distributed into other parts given by the
    numerical part size specifications). 
    """
    parts = []
    rest_index = None # remember where the 'rest' part is
    for i, part_spec in enumerate(split_spec.split('_')):
        if part_spec[-1] == "%":
            parts.append(int(round((int(part_spec[:-1]) / 100) * size)))
        elif part_spec[-1] == "#":
            parts.append(int(part_spec[:-1]))
        elif part_spec == 'rest' and rest_index == None:
            parts.append(0)
            rest_index = i
        else:
            raise ValueError("cannot parse specification '%s'" % split_spec)
    # check if it makes sense
    sum_parts = sum(parts)
    if sum_parts < size:
        diff = size - sum_parts
        if not rest_index == None:
            parts[rest_index] = diff
        else:
            sys.stderr.write("rounding: extra %d sentences will be added\n")
            sys.stderr.write("to part with the largest number of\n" % diff)
            sys.stderr.write("sentences. In case of a tie, the sentences\n")
            sys.stderr.write("are added to the first part.\n")
            parts[parts.index(max(parts))] += diff
    elif sum_parts == size:
        if not rest_index == None:
            sys.stderr.write("warning: 'rest' part will be empty\n")
    elif sum_parts > size:
        raise ValueError("treebank smaller than sum of split (%d vs %d)\n" \
                             % (size, sum_parts))
    return parts


def decorate_label(tree, **params):
    """Compute subtree label decorations depending on given parameters.
    """
    label = tree['label']
    gf_separator = DEFAULT_GF_SEPARATOR
    if 'gf_separator' in params:
        gf_separator = unicode(params['gf_separator'])
    gf_string = ""
    if 'gf' in params and not tree['edge'].startswith("-"):
        gf_string = "%s%s" % (gf_separator, tree['edge'])
    head = "" 
    if 'mark_heads_marking' in params and tree['head']:
        head = DEFAULT_HEAD_MARKER
    split_marker = ""
    if 'boyd_split_marking' in params and tree['split']:
        split_marker = "*"
    split_number = ""
    if 'boyd_split_numbering' in params and tree['split']:
        split_number = tree['block_number']
    return u"%s%s%s%s%s" % (label, gf_string, head, split_marker, split_number)


def replace_parens(tree):
    """Replace bracket characters in node data before bracketing output.
    """
    for arg in ['word', 'lemma', 'label', 'edge', 'morph']:
        tree[arg] = tree[arg].replace("(", "LRB")
        tree[arg] = tree[arg].replace(")", "RRB")
        tree[arg] = tree[arg].replace("[", "LSB")
        tree[arg] = tree[arg].replace("]", "RSB")
        tree[arg] = tree[arg].replace("{", "LCB")
        tree[arg] = tree[arg].replace("}", "RCB")
    return tree


def export_tabs(length):
    """Number of tabs after a single field in export format, given the
    length of the field. 
    """
    if length < 8:
        return "\t\t\t"
    elif length < 16:
        return "\t\t"
    else:
        return "\t"


def export_format(subtree, **params):
    """Return an export formatted node line for a given subtree.
    """
    if subtree['edge'] == None:
        subtree['edge'] = '--'
    label = decorate_label(subtree, **params)
    if not 'export_four' in params:
        return u"%s%s%s\t%s%s%s\t%d\n" \
            % (subtree['word'], 
               export_tabs(len(subtree['word'])), 
               label, 
               subtree['morph'], 
               export_tabs(len(subtree['morph']) + 8), 
               subtree['edge'], 
               subtree['parent']['num'])
    else:
        return u"%s%s%s%s%s\t%s%s%s\t%d\n" \
            % (subtree['word'], 
               export_tabs(len(subtree['word'])), 
               subtree['lemma'], 
               export_tabs(len(subtree['lemma'])), 
               label, 
               subtree['morph'], 
               export_tabs(len(subtree['morph']) + 8), 
               subtree['edge'], 
               subtree['parent']['num'])


def compute_export_numbering(tree):
    """We compute the 'level' of each node, i.e., its minimal path length to a
    terminal. We then distribute numbers >= 500 from left to right in each
    level, starting with the lowest one.
    """
    levels = {}
    for subtree in trees.preorder(tree):
        if trees.has_children(subtree):
            level = 0
            for terminal in trees.terminals(subtree):
                path_length = 0
                path_element = terminal
                while not path_element == subtree:
                    path_element = path_element['parent']
                    path_length += 1
                level = max(level, path_length)
            if not level in levels:
                levels[level] = []
            levels[level].append(subtree)
    for level in levels:
        levels[level] = sorted(levels[level], \
                                   key=lambda x: trees.terminals(x)[0]['num'])
    num = 500
    for level_num in sorted(levels.keys()):
        level = levels[level_num]
        for subtree in level:
            subtree['num'] = num
            num += 1
    tree['num'] = 0


def export(tree, stream, **params): 
    """Export format as in Brants (1997). 
    """
    # check parameters
    tree_id = tree['id']
    compute_export_numbering(tree)
    stream.write(u"#BOS %d\n" % tree_id)
    terms = {}
    non_terms = {}
    for subtree in trees.preorder(tree):
        if subtree == tree:
            continue
        subtree['parent_num'] = u"%d" % subtree['parent']['num']
        if trees.has_children(subtree):
            subtree['word'] = u"#%d" % subtree['num']
            non_terms[subtree['num']] = export_format(subtree, **params)
        else:
            terms[subtree['num']] = export_format(subtree, **params)
    for num in sorted(terms.keys()):
        stream.write(terms[num])
    for num in sorted(non_terms.keys()):
        stream.write(non_terms[num])
    stream.write(u"#EOS %d\n" % tree_id)


def write_brackets_subtree(tree, stream, **params):
    """Write a single bracketed subtree.
    """
    stream.write(u"(")
    if trees.has_children(tree):
        stream.write(decorate_label(tree, **params))
        for child in trees.children(tree):
            write_brackets_subtree(child, stream, **params)
    else:
        tree = replace_parens(tree)
        stream.write(decorate_label(tree, **params))
        stream.write(" %s" % tree['word'])
    stream.write(u")")


def brackets(tree, stream, **params):
    """One bracketed tree per line. Tree must not be discontinuous.
    """
    if (analyze.gap_degree(tree) > 0):
        raise ValueError("cannot write a discontinuous trees with brackets.")
    write_brackets_subtree(tree, stream, **params)
    stream.write(u"\n")


OUTPUT_FORMATS = [export, brackets]
OUTPUT_OPTIONS = {'boyd_split_marking' : 'Boyd split: Mark split nodes with *',
                  'boyd_split_numbering' : 'Boyd split: Number split nodes',
                  'export_four' : 'Export fmt: Use lemma (-- if not present)',
                  'gf' : 'Append grammatical function labels to node labels',
                  'gf_separator' : 'Separator to use for gf option', 
                  'mark_heads_marking' : 'Output head marking'}
