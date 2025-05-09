#!/usr/bin/env python3


"""
Requires: Python 3.7 or later (for install.py)
"""


from support.config import load_config
from install import Install, g_debug

import argparse
from collections.abc import Sequence
import sys
import traceback
import typing as tp


def uninstall(
    project_names: Sequence[str] = (), outf: tp.TextIO = sys.stdout,
    errf: tp.TextIO = sys.stderr
) -> bool:
    success = True
    config = load_config(outf)
    install = Install(outf=outf, errf=errf)
    if project_names:
        for name in project_names:
            path = config.proj_dir/name
            if path.exists():
                if path.is_dir():
                    success = install.delete_dir(path) and success
                else:
                    success = install.delete_file(path) and success
    else:
        path = config.app_sup_dir
        if path.exists():
            success = install.delete_dir(path)
    return success


def from_command_line(
    args: tp.Optional[Sequence[str]] = None
) -> Sequence[str]:
    ap = argparse.ArgumentParser(
        description="""
            Removes files, symlinks, and directories installed in
            "~/Library/Application Support" by install.py. Note that if they
            have already been uninstalled, the script does nothing and returns
            0 (success).
            """
    )
    ap.add_argument(
        "project_names", nargs="*",
        help="""
            If you provide the names of specific projects you want uninstalled,
            only these will be removed from the proj directory. Otherwise
            (with no names supplied), the whole automator_util directory is
            removed.
            """
    )
    res = ap.parse_args(args=args)
    return res.project_names if res.project_names else ()


if __name__ == "__main__":
    try:
        if not uninstall(project_names=from_command_line()):
            print("some errors were reported", file=sys.stderr)
            sys.exit(1)
    except Exception as err:
        print("ERROR:", err, file=sys.stderr)
        if g_debug:
            traceback.print_exc()
        sys.exit(3)
