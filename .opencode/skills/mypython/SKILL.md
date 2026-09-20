---
name: mypython
description: Use when writing, editing, or reviewing Python code in this repository. Ensures code matches the author's established style: camelCase methods, % formatting, custom docstrings, and no type hints.
---

# MyPython - Repository Coding Style

Write Python code that matches this repository's established conventions. Every rule below is derived from the existing codebase — follow them exactly.

---

## Naming

- **Classes**: PascalCase. One primary class per file, named after the file.
  - `class AppLauncher(threading.Thread):` in `AppLauncher.py`
  - `class DirectoryPlugin(IndexerObject):` in `DirectoryPlugin.py`
- **Methods**: camelCase. Never snake_case.
  - `def executeProgram(self, event):`
  - `def getExecutionString(self, index, startChar=""):`
  - `def loadAliases(self):`
- **Variables**: camelCase.
  - `self.queryQueue`, `self.pluginMap`, `self.hasShape`
- **Constants**: UPPER_CASE.
  - `APP_VERSION = "1.0.7"`, `DISPLAY = 101`, `REINDEX_IDLE = 1`
- **Private methods**: single-underscore prefix.
  - `def _reindex(self):`, `def _machineIsIdle(self):`
- **Event handlers**: `onXxx` or `evtXxx` prefix.
  - `def onHotKeyfunction(self, event):`, `def onCloseWindow(self, event):`
- **Instance state flags** that are mutable may use UPPER_CASE (mimicking constants):
  - `self.READY`, `self.RUNNING`, `self.STOPPED`

---

## Imports

Organize imports into comment-delimited groups. Use these exact headers:

```python
# Import standard modules
import os
import time

# Import 3rdparty modules
import wx

# Import own modules
from Config import Config
from Logger import Logger
```

Wildcard imports are acceptable for own modules: `from OwnConstants import *`

Do not alphabetize imports within each group.

---

## Docstrings

Use triple-quoted `"""` docstrings. Custom Google-like format with `=` for Args and `[TYPE]` annotations:

```python
def method(self, param1, param2):
    """
    One-line description of what this method does.
    Args:
      param1 = Description of first parameter
      param2 = Description of second parameter

    Returns: [TYPE] Description of return value
    """
```

If there are no arguments:

```python
def method(self):
    """
    Description of what this method does.
    Args: None

    Returns: [TYPE] Description of return value
    """
```

Types in docstrings go in square brackets: `[STRING]`, `[FLOAT]`, `[BOOLEAN]`, `[TUPLE]`, `[LIST]`.

`__init__` methods do NOT get a `Returns:` section. Constructors do not return values:

```python
class MyClass:
    """Brief description of the class."""

    def __init__(self, parent, config):
        """
        Initialize the class.
        Args:
          parent = The parent window
          config = The application config
        """

For class constructors `__init__`, include a docstring specifying that this is the constructor and its parameters BUT do not include a `Returns` section:
```python
def __init__(self, param1, param2):
    """
    Class constructor.
    Args:
      param1 = Description of first parameter
      param2 = Description of second parameter
    """
```

---

## String Formatting

Use `%` formatting exclusively. Never use f-strings or `.format()`:

```python
"About AL %s" % APP_VERSION
"%s WARNING: %s" % (self.getTimeStamp(), string)
"Image type unknown: %s" % filename
```

For multi-line strings, use backslash continuation with `+`:

```python
return "The new name of this entry already\n" \
       + "exists. Please choose a different one"
```

---

## Inheritance and Constructors

Call parent constructors explicitly by class name. Never use `super()`:

```python
class AlFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Al 0.1", style=windowStyle)

class Indexer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
```

---

## Error Handling

Catch specific exceptions when they can be handled with defaults or retries. Let unexpected exceptions propagate:

```python
# Catching with a default
try:
    value = config["someKey"]
except KeyError:
    value = "defaultValue"

# Catching with a retry
for attempt in range(3):
    try:
        result = networkCall()
        break
    except ConnectionError:
        time.sleep(1)
else:
    raise Exception("Failed after 3 attempts")

# Letting it fly — do NOT catch exceptions you cannot handle
def criticalOperation(self):
    result = self.loadData()  # exceptions propagate to caller
```

---

## File I/O

Use manual `open()`/`close()`. Never use `with` statements:

```python
fp = open(filename, "rb")
data = fp.read()
fp.close()

fp = open(self.filename, "w")
fp.write(content)
fp.close()
```

---

## Null Checks

Use `== None` and `!= None`. Never use `is None` or `is not None`:

```python
if widget == None:
    return

if iconPath != None:
    self.setIcon(iconPath)
```

---

## Iteration

Use `for i in range(0, len(x))` loops. Avoid `enumerate()`, `zip()`, `map()`, `filter()`, and list comprehensions:

```python
i = 0
for i in range(0, len(self.aliases)):
    self.lb.Insert(self.aliases[i][0], i)
    i += 1
```

---

## Line Continuation

Prefer backslash `\` for line continuation over parenthetical wrapping:

```python
windowStyle = wx.FRAME_SHAPED | wx.SIMPLE_BORDER \
              | wx.FRAME_NO_TASKBAR
```

---

## File Header

Include this box comment at the top of every file:

```python
###################################################
# Application : AL                                #
#  * Program to quickly launch other programs     #
#                                                 #
# Author      : <Author Name>                     #
# Date        : <HH:MM MM.DD.YYYY>                #
# License     : GNU General Public License (GPL)  #
###################################################
```

---

## File Structure

- One primary class per file, file named after the class.
- 4-space indentation (never tabs).
- Max line length ~100-120 characters.
- 1-2 blank lines between methods within a class.
- Include `if __name__ == "__main__":` blocks for testing class standalone when appropriate.

---

## Data Structures

Use plain lists and dictionaries. No dataclasses, no NamedTuples, no `__slots__`:

```python
# App = [indexString, What to execute(path)]
app = [appName, appPath, isAlias]

# Config directories: [path_list, enabled_bool, extensions_list]
```

---

## Do NOT Use

- Type hints or annotations
- Decorators (`@staticmethod`, `@classmethod`, `@property`, `@abstractmethod`)
- Context managers (`with` statements)
- `super()` calls
- f-strings or `.format()`
- `enumerate()`, `zip()`, `map()`, `filter()`
- List comprehensions
- `is None` / `is not None`
- Custom exception classes
- `__all__`
- Alphabetized imports

---

## Dynamic Instantiation

Use `getattr()` with a plugin registry dict. Never use `eval()` for dynamic instantiation:

```python
# Plugin registry
PLUGIN_MAP = {
    "DirectoryPlugin": DirectoryPlugin,
    "FirefoxPlugin": FirefoxPlugin,
    "AliasPlugin": AliasPlugin,
}

# Instantiation
plugin_class = PLUGIN_MAP.get(pluginName)
if plugin_class:
    self.plugins[pluginName] = plugin_class(self.config, indexer)
```

---

## Threading

Subclass `threading.Thread` directly. Use `threading.Event` for clean shutdown signaling:

```python
class MyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stopEvent = threading.Event()

    def run(self):
        while not self._stopEvent.is_set():
            self.doWork()
            self._stopEvent.wait(0.5)  # sleeps until stopped or timeout

    def stop(self):
        self._stopEvent.set()
        self.join()
```


