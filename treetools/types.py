"""Shared typing vocabulary for treetools.

The project predates static typing and deliberately keeps its public tree
representation as a mutable mapping.  These aliases describe that existing
representation without changing it at runtime, while protocols document the
callable boundaries used by readers, writers, and transformations.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping, MutableMapping
from typing import Any, Protocol, TextIO, TYPE_CHECKING, TypeAlias, TypedDict

if TYPE_CHECKING:
    from .trees import Tree


class NodeData(TypedDict, total=False):
    """Known keys stored in ``Tree.data``.

    ``total=False`` reflects the legacy readers, which add metadata as a tree
    moves through the pipeline.  The mapping remains open to format-specific
    keys at runtime for backwards compatibility.
    """

    word: str | None
    lemma: str | None
    label: str | None
    morph: str | None
    edge: str | None
    parent_num: int | str | None
    num: int | None
    sid: int | None
    head: bool
    split: bool
    head_block: bool
    block_number: int | str | None
    terminals: list[int]


NodeMapping: TypeAlias = MutableMapping[str, Any]
Params: TypeAlias = Mapping[str, Any]

Function: TypeAlias = tuple[str, ...]
VariableRef: TypeAlias = tuple[int, int]
Linearization: TypeAlias = tuple[tuple[VariableRef, ...], ...]
VerticalContext: TypeAlias = str | tuple[str, ...]
Grammar: TypeAlias = dict[
    Function, dict[Linearization, dict[VerticalContext, int]]
]
Lexicon: TypeAlias = dict[str, Counter[str]]
Sentence: TypeAlias = list[tuple[str | None, str | None]]


class TreeReader(Protocol):
    """Callable protocol implemented by tree input generators."""

    def __call__(
        self, in_file: str, in_encoding: str, **params: Any
    ) -> Iterator[Tree]: ...


class TreeWriter(Protocol):
    """Callable protocol implemented by per-tree output functions."""

    def __call__(
        self, tree: Tree, stream: TextIO, **params: Any
    ) -> None: ...


class Transform(Protocol):
    """Callable protocol for in-place tree transformations."""

    def __call__(self, tree: Tree, **params: Any) -> Tree | None: ...


class Analyzer(Protocol):
    """Protocol for stateful tree analysis tasks used by the CLI."""

    def run(self, tree: Tree) -> None: ...

    def done(self) -> None: ...


class GrammarReader(Protocol):
    """Callable protocol for grammar readers returning grammar and lexicon."""

    def __call__(
        self, src: str, src_enc: str, **opts: Any
    ) -> tuple[Grammar, Lexicon]: ...


class GrammarWriter(Protocol):
    """Callable protocol for grammar output functions."""

    def __call__(
        self,
        gram: Grammar,
        lexicon: Lexicon,
        dest: str,
        dest_enc: str,
        **params: Any,
    ) -> None: ...


class TransitionWriter(Protocol):
    """Callable protocol for transition output functions."""

    def __call__(
        self, trans: list[tuple[Sentence, list[Any]]], dest: str,
        dest_enc: str, **params: Any
    ) -> None: ...


TransformMap: TypeAlias = dict[str, Transform]


__all__ = [
    "Analyzer",
    "Function",
    "Grammar",
    "GrammarReader",
    "GrammarWriter",
    "Lexicon",
    "Linearization",
    "NodeData",
    "NodeMapping",
    "Params",
    "Sentence",
    "Transform",
    "TransformMap",
    "TransitionWriter",
    "TreeReader",
    "TreeWriter",
    "VariableRef",
    "VerticalContext",
]
