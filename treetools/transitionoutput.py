"""treetools: Tools for transforming treebank trees.

This module provides functions and classes for grammar output.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import annotations

import io
from typing import Any

from .types import Sentence, TransitionWriter


def plain(trans: list[tuple[Sentence, list[Any]]], dest: str,
          dest_enc: str, **params: Any) -> None:
    """Write plain transitions.
    """
    with io.open(u"%s" % dest, 'w', encoding=dest_enc) as trans_stream:
        for sent, seq in trans:
            if 'pos' in params:
                psent = ' '.join([u"%s" % pos for (word, pos) in sent])
            else:
                psent = ' '.join([u"%s" % word for (word, pos) in sent])
            pseq = ' '.join([u"%s" % t.pretty_print() for t in seq])
            trans_stream.write(u"%s ||| %s\n" % (psent, pseq))


FORMATS = [plain]
FORMAT_OPTIONS = {'pos': 'print out POS tags instead of words'}
FORMAT_MAP: dict[str, TransitionWriter] = {writer.__name__: writer
                                           for writer in FORMATS}
