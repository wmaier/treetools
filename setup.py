"""
treetools: Tools for transforming treebank trees.

Setup module.

Author: Wolfgang Maier <maierw@hhu.de>
"""
from __future__ import print_function
import sys
from setuptools import setup
from distutils.version import LooseVersion

classifiers = """\
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Science/Research
License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Text Processing :: Linguistic
"""

if LooseVersion(sys.version) < LooseVersion("3.7"):
    print("Requires Python version >= 3.7")
    sys.exit(1)

long_description = ""
with open("README.md") as readme_file:
    long_description = readme_file.read()
setup(name = "treetools",
      version = "0.3.0",
      description = "Tools for processing treebank trees",
      author = "Wolfgang Maier",
      author_email = "wolfgang.maier@gmail.com",
      url = "https://github.com/wmaier/treetools",
      license = "GPLv3 or later",
      platforms = ["any"],
      packages = ["trees"],
      scripts = ["treetools"],
      keywords = ["treebanks", "trees", "grammar"],
      download_url = "https://github.com/wmaier/treetools/archive/v0.3.0.tar.gz",
      classifiers = filter(None, classifiers.split("\n")),
      long_description = long_description,
)
