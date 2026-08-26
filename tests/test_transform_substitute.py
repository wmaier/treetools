"""Tests for terminal substitution transforms."""

from treetools import transform, trees


def test_substitute_terminals_quietly_skips_invalid_positions(
        cont_tree, tmp_path, capsys):
    substitutions = tmp_path / "substitutions.txt"
    substitutions.write_text("1 99 replacement NN\n", encoding="utf-8")
    original_words = [terminal.data['word']
                      for terminal in trees.terminals(cont_tree)]

    result = transform.substitute_terminals(
        cont_tree, terminalfile=str(substitutions), quiet=True)

    assert [terminal.data['word']
            for terminal in trees.terminals(result)] == original_words
    assert capsys.readouterr().out == ""
