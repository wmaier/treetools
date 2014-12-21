"""
treetools: Tools for transforming treebank trees.

setup module

Author: Wolfgang Maier <maierw@hhu.de>
"""
import sys
from distutils.core import setup
if sys.version < '2.7.3':
    print 'Requires Python version >= 2.7.3'
    sys.exit(1)
setup(name='treetools',
      version='0.1.0',
      description='Tools for processing treebank trees',
      author='Wolfgang Maier',
      author_email='wolfgang.maier@gmail.com',
      url='https://github.com/wmaier/treetools',
      license='GPLv3 or later',
      packages=['trees'],
      scripts=['treetools'],
      keyword=['treebanks', 'trees', 'grammar'],
      download_url='https://github.com/wmaier/treetools/tarball/0.1.0',
      classifiers=[],
)
