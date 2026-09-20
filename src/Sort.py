###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import standard modules
import functools

def _cmp_to_key(mycmp):
    """Convert a cmp= function into a key= function"""
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
    return K

# Case sensitive sorting
def sortStringTuple(list, index, reverse = False):
    """
    Method to sort a list of tuples by a given index
    Args:
      list = The list of tuples to sort
      index = The index to sort by
      reverse = If True, sort in reverse order

    Returns: None
    """
    def cmp_func(x, y):
        if y[index] < x[index]:
            return 1
        elif y[index] > x[index]:
            return -1
        return 0
    def cmp_func_r(x, y):
        if x[index] < y[index]:
            return 1
        elif x[index] > y[index]:
            return -1
        return 0
    if reverse:
        list.sort(key=_cmp_to_key(cmp_func))
    else:
        list.sort(key=_cmp_to_key(cmp_func_r))
        
# Case insensetive sorting
def sortStringTupleCI(list, index):
    """
    Method to sort a list of tuples by a given index, case insensitive
    Args:
      list = The list of tuples to sort
      index = The index to sort by

    Returns: None
    """
    def cmp_func(x, y):
        a = x[index].lower()
        b = y[index].lower()
        if a < b:
            return 1
        elif a > b:
            return -1
        return 0
    list.sort(key=_cmp_to_key(cmp_func))
