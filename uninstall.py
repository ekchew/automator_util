#!/usr/bin/env python3


"""
Requires: Python 3.7 or later (for dataclasses)
"""


from support.config import load_config
from install import Install, g_debug

import sys
import traceback
import typing as tp


def uninstall(
    outf: tp.TextIO = sys.stdout, errf: tp.TextIO = sys.stderr
) -> bool:
    config = load_config()
    path = config.app_sup_dir
    if path.exists():
        return Install(outf=outf, errf=errf).delete_dir(path)
    else:
        return True


if __name__ == "__main__":
    try:
        if not uninstall():
            print("some errors were reported", file=sys.stderr)
            sys.exit(1)
    except Exception as err:
        print("ERROR:", err, file=sys.stderr)
        if g_debug:
            traceback.print_exc()
        sys.exit(3)
