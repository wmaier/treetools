"""
treetools: Tools for transforming treebank trees.

Unit tests (pytest) for tree operations

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
from trees import misc, transform


sample = "\x1b[1msample_func\x1b[0m\n\x1b[1m-----------\x1b[0m\nReattach some children of the virtual root node in NeGra/TIGER/TueBa-DZ.\n    In a nutshell, the algorithm moves all children of VROOT to the least\n    common ancestor of the left neighbor terminal of the leftmost terminal and\n    the right neighbor terminal of the rightmost terminal they dominate. We\n    iterate through the children of VROOT left to right. Therefore, we might\n    have to skip over adjacent children of VROOT on the right (which are not\n    attached yet) in order to find the rightmost terminal. If the VROOT child\n    constitutes the start or end of the sentence, or if the least common\n    ancestor as described above is VROOT, it is not moved.\n\n    Prerequisite: none\n    Parameters: none\n    Output options: none\n    "


def sample_func():
    """Reattach some children of the virtual root node in NeGra/TIGER/TueBa-DZ.
    In a nutshell, the algorithm moves all children of VROOT to the least
    common ancestor of the left neighbor terminal of the leftmost terminal and
    the right neighbor terminal of the rightmost terminal they dominate. We
    iterate through the children of VROOT left to right. Therefore, we might
    have to skip over adjacent children of VROOT on the right (which are not
    attached yet) in order to find the rightmost terminal. If the VROOT child
    constitutes the start or end of the sentence, or if the least common
    ancestor as described above is VROOT, it is not moved.

    Prerequisite: none
    Parameters: none
    Output options: none
    """
    pass


sample_options = {'disco_reordered' : 'In discobrackets, output CF order with '\
                     'terminal indices',
                 'gf_split' : 'Brackets: Try to split grammatical ' \
                     'functions from label at last occurrence of gf separator',
                 'gf_separator' : 'Brackets: Separator to use for ' \
                     ' gf option (default %s)' % "-",
                 'brackets_emptypos' : 'Brackets: Allow empty POS tags',
                 'brackets_firstid' : 'Brackets: Give first tree id [ID]',
                 'continuous' : 'Export/TIGERXML: number sentences by ' \
                     'counting, don\'t use #BOS',
                 'replace_parens' : 'Replace parens by LRB, RRB, etc. ',
                 'quiet' : 'no messages while reading'}


sample_opts_formatted = "\x1b[1mbrackets_emptypos\x1b[0m       Brackets: Allow empty POS tags\n\x1b[1mbrackets_firstid\x1b[0m        Brackets: Give first tree id [ID]\n\x1b[1mcontinuous\x1b[0m              Export/TIGERXML: number sentences by counting, don't\n                        use #BOS\n\x1b[1mdisco_reordered\x1b[0m         In discobrackets, output CF order with terminal indices\n\x1b[1mgf_separator\x1b[0m            Brackets: Separator to use for  gf option (default -)\n\x1b[1mgf_split\x1b[0m                Brackets: Try to split grammatical functions from label\n                        at last occurrence of gf separator\n\x1b[1mquiet\x1b[0m                   no messages while reading\n\x1b[1mreplace_parens\x1b[0m          Replace parens by LRB, RRB, etc. \n"


def test_grouper():
    r = []
    for element in misc.grouper(3, 'ABCDEFG', 'x'):
        r.append(element)
    assert(r == [("A", "B", "C"), ("D", "E", "F"), ("G", "x", "x")])


def test_bold():
    sample = '\033[1m{}\033[0m'.format("Test") 
    test = misc.bold("Test")
    assert(sample == test)


def test_make_headline():
    test = "Test"
    sample = misc.bold("{}\n{}\n".format(test, "=" * len(test)))
    comp = misc.make_headline(test)
    assert(sample == comp)


def test_get_doc():
    comp = misc.get_doc([sample_func])
    assert sample == comp


def test_get_doc_opts():
    comp = misc.get_doc_opts(sample_options)
    assert sample_opts_formatted == comp


def test_options_dict():
    input = ["a:b", "c:d", "e:1"]
    sample = {"a" : "b", "c" : "d", "e" : 1}
    assert misc.options_dict(input) == sample