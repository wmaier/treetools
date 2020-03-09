"""treetools: Tools for transforming treebank trees.

conftest.py setup for py.test

Author: Wolfgang Maier <maierw@hhu.de>
"""
import pytest
import tempfile
import os
from . import testdata
from trees import trees, treeinput


@pytest.fixture(scope='function',
                params=[(treeinput.tigerxml, testdata.SAMPLE_TIGERXML, {}),
                        (treeinput.export, testdata.SAMPLE_EXPORT, {})])
def discont_tree(request):
    """
    Load discontinuous tree samples.
    """
    tempfile_name = None
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        tempfile_name = temp.name
        temp.write(request.param[1])
        temp.flush()
    request.param[2]['quiet'] = True
    reader = request.param[0](tempfile_name, 'utf8', **request.param[2])

    def fin():
        os.remove(tempfile_name)
    request.addfinalizer(fin)
    return next(reader)


@pytest.fixture(scope='function',
                params=[(treeinput.brackets, testdata.SAMPLE_BRACKETS, {}),
                        (treeinput.brackets, testdata.SAMPLE_BRACKETS_TOL,
                         {'brackets_emptypos': True})])
def cont_tree(request):
    """
    Load continuous tree samples.
    """
    tempfile_name = None
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        tempfile_name = temp.name
        temp.write(request.param[1])
        temp.flush()
    request.param[2]['quiet'] = True
    reader = request.param[0](tempfile_name, 'utf8', **request.param[2])

    def fin():
        os.remove(tempfile_name)
    request.addfinalizer(fin)
    tree = next(reader)
    # 'fix' POS tags for brackets_emptypos mode
    terms = trees.terminals(tree)
    if all([term.data['label'] == trees.DEFAULT_LABEL for term in terms]):
        for term, pos in zip(terms, testdata.POS):
            term.data['label'] = pos
    return tree
