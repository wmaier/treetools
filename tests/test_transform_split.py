"""Tests for split transformation output."""

from types import SimpleNamespace

from treetools import transform, treeinput
from . import testdata


def test_split_tigerxml_output_is_a_complete_document(tmp_path):
    source = tmp_path / "source.xml"
    destination = tmp_path / "trees.xml"
    source.write_text(testdata.SAMPLE_TIGERXML, encoding="utf-8")
    args = SimpleNamespace(
        src=str(source), dest=str(destination),
        src_format='tigerxml', dest_format='tigerxml',
        src_enc='utf-8', dest_enc='utf-8',
        src_opts=[], dest_opts=[], trans=[], params=[],
        split='1#', counting=100)

    transform.run(args)

    trees = list(treeinput.tigerxml(
        str(tmp_path / "trees.xml.0"), "utf-8", quiet=True))
    assert len(trees) == 1
