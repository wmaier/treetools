"""Tests for the transformation command workflow."""

from types import SimpleNamespace

import pytest

from treetools import transform
from . import testdata


def test_run_rejects_identical_source_and_destination(tmp_path):
    source = tmp_path / "trees.brackets"
    source.write_text(testdata.SAMPLE_BRACKETS, encoding="utf-8")
    args = SimpleNamespace(
        src=str(source), dest=str(source),
        src_format='brackets', dest_format='brackets',
        src_enc='utf-8', dest_enc='utf-8',
        src_opts=[], dest_opts=[], trans=[], params=[],
        split='', counting=100)

    with pytest.raises(ValueError, match="source and destination"):
        transform.run(args)

    assert source.read_text(encoding="utf-8") == testdata.SAMPLE_BRACKETS
