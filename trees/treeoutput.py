"""
treetools: Tools for transforming treebank trees.

This module handles tree writing in different formats.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import division, print_function
import sys
from math import floor
from xml.sax.saxutils import quoteattr
from . import trees, treeanalysis
# In Python 3.5, unicode() does not exist anymore, just str()
try:
    type(unicode)
except NameError:
    def unicode(s): return str(s)


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
    rest_index = None  # remember where the 'rest' part is
    for i, part_spec in enumerate(split_spec.split('_')):
        if part_spec[-1] == "%":
            parts.append(int(floor((int(part_spec[:-1]) / 100) * size)))
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
            sys.stderr.write("rounding: extra %d sentences will be\n" % diff)
            sys.stderr.write("added to part with the largest number of\n")
            sys.stderr.write("sentences. In case of a tie, the sentences\n")
            sys.stderr.write("are added to the first part.\n")
            parts[parts.index(max(parts))] += diff
    elif sum_parts == size:
        if not rest_index == None:
            sys.stderr.write("warning: 'rest' part will be empty\n")
    elif sum_parts > size:
        raise ValueError("treebank smaller than sum of split (%d vs %d)\n"
                         % (size, sum_parts))
    return parts


def export_begin(stream, **params):
    """Export preamble of output is empty.
    """
    pass


def export_end(stream, **params):
    """Export suffix of output is empty.
    """
    pass


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
    if subtree.data['edge'] == None:
        subtree.data['edge'] = '--'
    label = trees.get_label(subtree, **params)
    if not 'export_four' in params:
        if subtree.data['morph'] == None:
            subtree.data['morph'] = "--"
        return u"%s%s%s\t%s%s%s\t%d\n" \
            % (subtree.data['word'],
               export_tabs(len(subtree.data['word'])),
               label,
               subtree.data['morph'],
               export_tabs(len(subtree.data['morph']) + 8),
               subtree.data['edge'],
               subtree.parent.data['num'])
    else:
        return u"%s%s%s%s%s\t%s%s%s\t%d\n" \
            % (subtree.data['word'],
               export_tabs(len(subtree.data['word'])),
               subtree.data['lemma'],
               export_tabs(len(subtree.data['lemma'])),
               label,
               subtree.data['morph'],
               export_tabs(len(subtree.data['morph']) + 8),
               subtree.data['edge'],
               subtree.parent.data['num'])


def compute_export_numbering(tree):
    """We compute the 'level' of each node, i.e., its minimal path length to a
    terminal. We then distribute numbers >= 500 from left to right in each
    level, starting with the lowest one.
    """
    levels, _ = trees.levels(tree)
    for level in levels:
        levels[level] = sorted(levels[level],
                               key=lambda x: trees.terminals(x)[0].data['num'])
    num = 500
    for level_num in sorted(levels.keys()):
        level = levels[level_num]
        for subtree in level:
            subtree.data['num'] = num
            num += 1
    tree.data['num'] = 0


def export(tree, stream, **params):
    """Export format as in Brants (1997).
    """
    # check parameters
    tree_id = tree.data['sid']
    compute_export_numbering(tree)
    stream.write(u"#BOS %d\n" % tree_id)
    terms = {}
    non_terms = {}
    for subtree in trees.preorder(tree):
        if subtree == tree:
            continue
        subtree.data['parent_num'] = u"%d" % subtree.parent.data['num']
        if trees.has_children(subtree):
            subtree.data['word'] = u"#%d" % subtree.data['num']
            non_terms[subtree.data['num']] = export_format(subtree, **params)
        else:
            terms[subtree.data['num']] = export_format(subtree, **params)
    for num in sorted(terms.keys()):
        stream.write(terms[num])
    for num in sorted(non_terms.keys()):
        stream.write(non_terms[num])
    stream.write(u"#EOS %d\n" % tree_id)


def brackets_begin(stream, **params):
    """Brackets preamble of output is empty.
    """
    pass


def brackets_end(stream, **params):
    """Brackets suffix of output is empty.
    """
    pass


def write_brackets_subtree(tree, stream, **params):
    """Write a single bracketed subtree.
    """
    stream.write(u"(")
    if trees.has_children(tree):
        if not 'brackets_emptyroot' in params:
            stream.write(trees.get_label(tree, **params))
        else:
            del params['brackets_emptyroot']
        for child in trees.children(tree):
            write_brackets_subtree(child, stream, **params)
    else:
        tree = trees.replace_chars(tree, trees.BRACKETS)
        stream.write(trees.get_label(tree, **params))
        stream.write(u" %s" % tree.data['word'])
    stream.write(u")")


def brackets(tree, stream, **params):
    """One bracketed tree per line. Tree must not be discontinuous.
    """
    if treeanalysis.gap_degree(tree) > 0:
        if 'brackets_skipdisco' in params:
            print("skipping discontinuous tree", file=sys.stderr)
        else:
            raise ValueError("cannot write a discontinuous trees with brackets.")
    else:
        write_brackets_subtree(tree, stream, **params)
        stream.write(u"\n")


def discobrackets_begin(stream, **params):
    """Discobrackets output preamble is empty.
    """
    pass


def discobrackets_end(stream, **params):
    """Discobrackets output suffix is empty.
    """
    pass


def discobrackets(tree, stream, **params):
    """One bracketed tree per line. Terminals are substituted for
    numbers and sentence is written after the tree in the same line,
    separated from the tree by a tab (terminal space-separated).
    """
    terminals = trees.terminals(tree)
    sentence = ' '.join([terminal.data['word'] for terminal in terminals])
    for terminal in terminals:
        terminal.data['word'] = unicode(terminal.data['num'])
    write_brackets_subtree(tree, stream, **params)
    stream.write("\t" + sentence + "\n")


def terminals_begin(stream, **params):
    """Terminals output preamble is empty.
    """
    pass


def terminals_end(stream, **params):
    """Terminals output suffix is empty.
    """
    pass


def terminals(tree, stream, **params):
    """All terminals of the tree on one line separated by whitespace.
    """
    if 'terminals_pos' in params and 'pos_only' in params:
        raise ValueError("can only use one of terminals_pos, pos_only")
    for terminal in trees.terminals(tree):
        if 'terminals_one' in params:
            if 'pos_only' in params:
                result = terminal.data['label']
            else:
                result = terminal.data['word']
                if 'terminals_pos' in params:
                    result += "\t%s" % terminal.data['label']
            print(result, file=stream)
        else:
            if 'pos_only' in params:
                result = terminal.data['label']
            else:
                result = terminal.data['word']
                if 'terminals_pos' in params:
                    result += "/%s" % terminal.data['label']
            print(unicode(result), end=u" ", file=stream)
    print(u"", file=stream)


def tigerxml_begin(stream, **params):
    """The start of a tigerxml document. To be completed.
    """
    stream.write(u"<?xml version='1.0'?>\n")
    stream.write(u"<corpus>\n")
    stream.write(u"<body>\n")


def tigerxml_end(stream, **params):
    """The end of a tigerxml document, to be completed.
    """
    stream.write(u"</body>\n")
    stream.write(u"</corpus>")


def tigerxml(tree, stream, **params):
    """A single sentence as TIGER XML. The IDs should probably
    be more fancy.
    """
    compute_export_numbering(tree)
    stream.write(u"<s id=\"%d\">\n" % tree.data['sid'])
    stream.write(u"<graph root=\"%s\">\n" % tree.data['num'])
    stream.write(u"  <terminals>\n")
    for terminal in trees.terminals(tree):
        stream.write(u"    <t id=\"%d\" " % terminal.data['num'])
        for field in ['word', 'lemma', 'label', 'morph']:
            terminal.data[field] = quoteattr(terminal.data[field])
        stream.write(u"%s=%s " % ('word', terminal.data['word']))
        stream.write(u"%s=%s " % ('lemma', terminal.data['lemma']))
        stream.write(u"%s=%s " % ('pos', terminal.data['label']))
        stream.write(u"%s=%s " % ('morph', terminal.data['morph']))
        stream.write(u"/>\n")
    stream.write(u"  </terminals>\n")
    stream.write(u"  <nonterminals>\n")
    for subtree in trees.postorder(tree):
        if trees.has_children(subtree):
            stream.write(u"    <nt id=\"%d\" cat=%s>\n"
                         % (subtree.data['num'],
                            quoteattr(subtree.data['label'])))
            for child in trees.children(subtree):
                stream.write(u"      <edge label=%s idref=\"%d\" />\n"
                             % (quoteattr(child.data['edge']),
                                child.data['num']))
            stream.write(u"    </nt>\n")
    stream.write(u"  </nonterminals>\n")
    stream.write(u"</graph>\n")
    stream.write(u"</s>\n")


OUTPUT_FORMATS = [export, brackets, discobrackets, tigerxml, terminals]
OUTPUT_OPTIONS = {'boyd_split_marking': 'Boyd split: Mark split nodes with *',
                  'boyd_split_numbering': 'Boyd split: Number split nodes',
                  'brackets_emptyroot': 'Omit root label as in Penn Treebank',
                  'brackets_skipdisco': 'Skip disco trees in brackets output',
                  'export_four': 'Export fmt: Use lemma (-- if not present)',
                  'gf': 'Append grammatical function labels to node labels',
                  'gf_separator': 'Separator to use for gf option',
                  'gf_terminals': 'If gf is set, use func. labels on terms.',
                  'mark_heads_marking': 'Output head marking',
                  'terminals_one': 'Terminals output with one terminal/line',
                  'terminals_pos': 'POS tags in terminal output (sep /)'}
