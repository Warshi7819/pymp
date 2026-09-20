###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Create a curry class used to supply arguments to button events
# Based on an example from the pythonCookbook
# http://aspn.activestate.com/ASPN/Python/Cookbook/
class curry:
     # Class constructor
     # ARGS:
     #   *args =
     #   **kwargs =
     def __init__(self, fun, *args, **kwargs):
          self.fun = fun
          self.pending = args[:]
          self.kwargs = kwargs.copy()

     # Override call
     # ARGS:
     #   *args =
     #   **kwargs =
     def __call__(self, *args, **kwargs):
          if kwargs and self.kwargs:
               kw = self.kwargs.copy()
               kw.update(kwargs)
          else:
               kw = kwargs or self.kwargs

          return self.fun(*(self.pending + args), **kw)
