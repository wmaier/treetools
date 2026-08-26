[![PyPI version](https://badge.fury.io/py/treetools.svg)](https://badge.fury.io/py/treetools)
[![Github All Releases](https://img.shields.io/github/downloads/kotlin-graphics/kotlin-unsigned/total.svg)]()

# treetools - tree processing

treetools is a collection of tools for processing treebank trees. It contains algorithms for tree manipulation (such as removal of  crossing branches), tree analysis, and grammar extraction.

treetools has been developed at the Department for Computational Linguistics at the Institute for Language and Information at the University of Düsseldorf, Germany (see <http://phil.hhu.de/beyond-cfg>). The project is sponsored by Deutsche Forschungsgemeinschaft (DFG). It is maintained by Wolfgang Maier.

Author: Wolfgang Maier <mailto:maierw@hhu.de>.
Contributions: Kilian Gebhardt 

## Installation

Requirements:

-  Python 3.11+

### From PyPI

To install the latest release from the Python package index, type::

    pip install treetools

### Development Installation

To set up a development environment, first install [uv](https://docs.astral.sh/uv/). On macOS with Homebrew::

    brew install uv

Or using pip::

    pip install uv

Then clone the repository and sync dependencies::

    git clone https://github.com/wmaier/treetools.git
    cd treetools
    uv sync

## Running

### Syntax

To run treetools, type::

    treetools-cli [subcommand] [parameters] [options]

Available subcommands are:

-  ``transform``: Process treebank trees. Run transformations and convert between different formats.
-  ``grammar``: Extract grammars for different parsers from treebanks.
-  ``treeanalysis``: Analyze certain properties of treebank trees, such as, e.g., gap degree.
-  ``transitions``: Extract transition sequences as used by transition-based parsers.

To get see the available parameters for a subcommand, type::

    treetools-cli [subcommand] --help

To get verbose help on available transformation algorithms, available options, etc., type::

    treetools-cli [subcommand] --usage

### Examples

To attach the punctuation in TIGER and remove its crossing branches while converting it from TigerXML to the export format, type::

    treetools-cli transform tiger.xml tiger.continuous.export --trans root_attach negra_mark_heads boyd_split raising --src-format tigerxml --dest-format export

To extract the bare sentences (one per line) from a treebank in bracketed format, such as the Penn Treebank, type::

    treetools-cli transform treebank.brackets treebank.terminals --src-format brackets --dest-format terminals

To delete the traces and co-indexation from the Penn Treebank, type::

    treetools-cli transform ptb ptb.notrace --transform ptb_transform --src-format brackets --dest-format brackets

To extract an left-to-right binarized LCFRS with v1/h2 markovization in rparse format from an export-format treebank, type::

    treetools-cli grammar input_treebank output_grammar leftright --dest-format rcg --markov v:1 h:2

## Development

### Running Tests

To run tests with the development environment, type::

    uv run pytest

### Type Checking

The typed tree core is checked with mypy while the remaining legacy modules
are migrated incrementally:

    uv run mypy

### Installing New Packages

To add a new package to your development environment, type::

    uv add <package-name>

For development-only dependencies (like testing tools), use::

    uv add --dev <package-name>

This will update both `pyproject.toml` and `uv.lock` automatically.

### License

The code is released under the GNU General Public Licence (GPL) 3.0 or higher. The license texts can be found at at
<http://www.gnu.org/licenses/gpl-3.0>. 
