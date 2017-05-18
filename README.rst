=====================================================================
 treetools - tree processing
=====================================================================

treetools is a collection of tools for processing treebank trees. It contains algorithms for tree manipulation (such as removal of  crossing branches), tree analysis, and grammar extraction.

treetools has been developed at the Department for Computational Linguistics at the Institute for Language and Information at the University of Düsseldorf, Germany (see http://phil.hhu.de/beyond-cfg). The project is sponsored by Deutsche Forschungsgemeinschaft (DFG). It is maintained by Wolfgang Maier.

Author: Wolfgang Maier <maierw@hhu.de>.
Contributions: Kilian Gebhardt 

.. contents::


Installation
============

Requirements:

- Python 2.7.3+/3.4+

To install the latest release from the Python package index, type::

    pip install treetools --user

To install the latest version clone the git repository and run::

    python setup.py install --user

within the repository directory. 

If you have superuser privileges and want to perform a system-wide installation, omit the `--user` option, respectively. 

Running
=======

Syntax
------

To run treetools, type::

    treetools [subcommand] [parameters] [options]

Available subcommands are:

- ``transform``: Process treebank trees. Run transformations and convert between different formats.
- ``grammar``: Extract grammars for different parsers from treebanks.
- ``treeanalysis``: Analyze certain properties of treebank trees, such as, e.g., gap degree.

To get see the available parameters for a subcommand, type::

    treetools [subcommand] --help

To get verbose help on available transformation algorithms, available options, etc., type::

    treetools [subcommand] --usage

Examples
--------

To attach the punctuation in TIGER and remove its crossing branches while converting it from TigerXML to the export format, type::

    treetools transform tiger.xml tiger.continuous.export --trans root_attach negra_mark_heads boyd_split raising --src-format tigerxml --dest-format export

To extract the bare sentences (one per line) from a treebank in bracketed format, such as the Penn Treebank, type::

    treetools transform treebank.brackets treebank.terminals --src-format brackets --dest-format terminals

To delete the traces and co-indexation from the Penn Treebank, type::

    treetools transform ptb ptb.notrace --transform ptb_transform --src-format brackets --dest-format brackets

To extract an left-to-right binarized LCFRS with v1/h2 markovization in rparse format from an export-format treebank, type::

    treetools grammar input_treebank output_grammar leftright --dest-format rcg --markov v:1 h:2


License
=======

The code is released under the GNU General Public Licence (GPL) 3.0 or higher. The license texts can be found at at
http://www.gnu.org/licenses/gpl-3.0. 

