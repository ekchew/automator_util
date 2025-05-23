#!/usr/bin/env python3


"""
This script saves a preference value to file.

It expects 3 positional args:
    1. the preference file name
    2. the preference key
    3. the corresponding value

Note that the value gets echoed back to stdout so that you can keep using it
in subsequent Automator actions if you like. However, as with get_pref.py,
any end-of-line characters will be escaped.

Requires: Python 3.4 or later (for pathlib)
"""


import json
from pathlib import Path
import sys


file_name, key, val = sys.argv[1:4]
key = key.strip()
val = val.rstrip()

# Build a path to the preferences file.
if not file_name.endswith(".json"):
    file_name = file_name + ".json"
path = Path.home()/"Library"/"Preferences"/file_name

# Attempt to load the JSON object from the file if it exists. Otherwise, begin
# with an empty `dict` as the object.
if path.is_file():
    with open(path, encoding="utf-8") as fp:
        obj = json.load(fp)
else:
    obj = {}

# Update `obj` with the new key/value and write it in JSON format to the
# preferences file.
obj[key] = val
with open(path, "w", encoding="utf-8") as fp:
    json.dump(obj, fp, ensure_ascii=False, indent=1)

# Print `val` to stdout as a single line arg.
print(val.replace("\n", r"\n"))
