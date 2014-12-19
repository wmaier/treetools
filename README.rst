=====================================================================
 treetools - tree processing
=====================================================================

treetools is a collection of tools for processing constituency
treebank trees. It contains algorithms for tree manipulation (such
as removal of crossing branches), tree analysis, and grammar 
extraction.

treetools is being developed and maintained at the Department for
Computational Linguistics at the Institute for Language and
Information at the University of Düsseldorf, Germany (see
http://phil.hhu.de/beyond-cfg). The project is sponsored by Deutsche
Forschungsgemeinschaft (DFG). 

Author: Wolfgang Maier <maierw@hhu.de>.

.. contents::


Installation
============

Requirements:

- Python 2.7.3+       

To install the latest version clone the git repository and run::

    python setup.py install --user

within the repository directory. If you have superuser privileges and
want to perform a system-wide installation, omit the `--user` option.

Running
=======

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


License
=======

The code is released under the GNU General Public Licence (GPL) 3.0 or
higher. The license texts can be found at at
http://www.gnu.org/licenses/gpl-3.0. 

