#!/usr/bin/env python3


"""
This script saves a preferences file containing a JSON list of values.

Its first arg should be the file name itself, followed by the preference values
in the remaining args.

Note that the preference values get echoed back to stdout so that you can
continue to work with them in subsequent Automator actions if you like.

Requires: Python 3.4 or later (for pathlib)
"""


import json
from pathlib import Path
import sys


file_name = sys.argv[1]
prefs = sys.argv[2:]
path = Path.home()/"Library"/"Preferences"/file_name
with open(file_name, "w", encoding="utf-8") as fp:
    json.dump(prefs, fp, ensure_ascii=False, indent=1)

for pref in prefs:
    print(pref.rstrip())
