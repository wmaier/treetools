""" 
treetools: Tools for transforming treebank trees.

This module provides misc utility functions.

Author: Wolfgang Maier <maierw@hhu.de>
"""


def get_doc(funs):
    """Generate a string from the names and docstrings of a list of given
    functions.
    """
    return "\n".join(["%s\n%s\n%s" % (bold(fun.__name__), 
                                      bold("-" * len(fun.__name__)),
                                      str(fun.__doc__)) 
                      for fun in funs])


def get_doc_opts(opts):
    """Generate a string from a dict with names and short explanations.
    """
    result = []
    for key in sorted(opts.keys()):
        exps = [opts[key]]
        while len(exps[-1]) > 56:
            last_space = exps[-1][:56].rfind(' ')
            splitted = [exps[-1][:last_space], exps[-1][last_space + 1:]]
            del exps[-1]
            exps += splitted
        result.append("%s%s%s" % (bold(key), " " * (24 - len(key)), exps[0]))
        for exp in exps[1:]:
            result.append("%s%s" % (" " * 24, exp))
    return "\n".join(result) + "\n"


def options_dict(options):
    """Given a list of key/value pairs with the key separated from the resp.
    value by a colon, return a dict with the pairs in which 
       - True is inserted for each key with no value
       - int() is called on all values for which isdigit() holds
    """
    result = {}
    for option in options:
        colon_index = option.index(':') if ':' in option else -1
        if colon_index > -1:
            option = option.strip().split(':')
            if option[1].isdigit():
                option[1] = int(option[1])
            result[option[0]] = option[1]
        else:
            result[option] = True
    return result


def bold(text):
    """For getting bold text on the command line (ANSI).
    """
    return u'\033[1m%s\033[0m' % text
