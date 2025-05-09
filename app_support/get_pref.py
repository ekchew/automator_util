#!/usr/bin/env python3


r"""
This script can return a preference value you set earlier with `set_pref.py`.

It expects a minimum of 2 positional args:
    1. the preference file name
    2. the preference key

You can also supply an optional 3rd arg:
    3. the default preference value

If you omit this and the look-up fails, the script will print a blank line.

In any case, the script will print a single line to stdout containing a value
that can be used in subsequent Automator actions.

Note that if the value contains any end-of-line characters, these will be
escaped as \n to avoid printing multiple lines. You may need to unescape these
later. (Automator treats each line printed to stdout as an individual arg being
passed to the next action, and so having multiple lines would result in a list
of args going out rather than a single one.)

Requires: Python 3.4 or later (for pathlib)
"""


import json
from pathlib import Path
import sys


# Parse the command line args.
file_name, key = sys.argv[1:3]
key = key.strip()
val = sys.argv[3].rstrip() if len(sys.argv) > 3 else ""

# Build a path to the preferences file.
if not file_name.endswith(".json"):
    file_name = file_name + ".json"
path = Path.home()/"Library"/"Preferences"/file_name

# If the file exists, load its JSON object contents.
if path.exists():
    with open(path, encoding="utf-8") as fp:
        obj = json.load(fp)
    val = obj.get(key, val)

# Print `val` to stdout as a single line arg.
print(val.replace("\n", r"\n"))
