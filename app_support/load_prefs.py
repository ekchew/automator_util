#!/usr/bin/env python3


r"""
This script loads back preferences that were saved by `save_prefs.py`.

Its first arg should be the file name itself, followed by default values for
all the preference values in the remaining args.

Once loaded, the values get printed to stdout with one value per line. A
subsequent Automator action could then input them as a list of args. (Note that
if a value is a string containing end-of-line characters, these will get
escaped as "\n". This is done to prevent a single value from being interpreted
as more than one by the next action, but you may need to unescape them later.)

Requires: Python 3.4 or later (for pathlib)
"""


import json
from pathlib import Path
import sys


file_name = sys.argv[1]
path = Path.home()/"Library"/"Preferences"/file_name
if path.exists():
    with open(file_name, encoding="utf-8") as fp:
        prefs = json.load(fp)
else:
    prefs = sys.argv[2:]

for pref in prefs:
    if isinstance(pref, str):
        pref = pref.rstrip().replace("\n", r"\n")
    print(pref)
