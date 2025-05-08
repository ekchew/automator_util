#!/usr/bin/env python3


"""
Requires: Python 3.7 or later (for dataclasses)
"""


from support.config import load_config

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
import os
from pathlib import Path
import shlex
import shutil
import sys
from traceback import print_exc
import typing as tp


g_debug: bool = False


@dataclass
class Install:
    projects: Sequence[Path] = field(default_factory=list)
    copy_mode: bool = False
    outf: tp.TextIO = sys.stdout
    errf: tp.TextIO = sys.stderr

    def run(self) -> bool:
        config = load_config()
        self.require_dir(config.app_sup_dir)
        success = self.sync(
            src_path=Path(__file__).parent/"app_support",
            dst_path=config.app_sup_dir
        )
        for proj in self.projects:
            success = self.sync(
                src_path=proj,
                dst_path=config.proj_dir/proj.name,
                delete=True
            ) and success
        return success

    def sync(
        self, src_path: Path, dst_path: Path, delete: bool = False
    ) -> bool:
        success = True
        self.require_dir(dst_path.parent)
        if dst_path.exists():
            if not dst_path.is_symlink():
                if src_path.is_dir():
                    src_set = set(src_path.iterdir())
                    dst_set = set(dst_path.iterdir())
                    for subpath in src_set:
                        success = self.sync(
                            src_path=subpath,
                            dst_path=dst_path/subpath.name,
                            delete=delete
                        ) and success
                    if delete:
                        for subpath in dst_set - src_set:
                            if subpath.is_dir():
                                success = self.delete_dir(subpath) and success
                            else:
                                success = self.delete_file(subpath) and success
                else:
                    src_stat = src_path.stat()
                    dst_stat = dst_path.stat()
                    if src_stat.st_size != dst_stat.st_size or \
                            src_stat.st_mtime > dst_stat.st_mtime:
                        success = self.delete_file(dst_path) \
                            and self.copy_file(src_path, dst_path)
        elif self.copy_mode:
            if src_path.is_dir():
                success = self.copy_dir(src_path, dst_path)
            else:
                success = self.copy_file(src_path, dst_path)
        else:
            success = self.make_symlink(
                link_path=dst_path, target_path=src_path
            )
        return success

    def copy_file(self, src_path: Path, dst_path: Path) -> bool:
        print(
            "copying file", quoted_path(src_path),
            "to", quoted_path(dst_path), file=self.outf
        )
        try:
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as err:
            print("ERROR:", err, file=self.errf)
            if g_debug:
                print_exc(file=self.errf)
            return False

    def copy_dir(self, src_path: Path, dst_path: Path) -> bool:
        print(
            "copying directory", quoted_path(src_path),
            "to", quoted_path(dst_path), file=self.outf
        )
        try:
            shutil.copytree(src_path, dst_path)
            return True
        except Exception as err:
            print("ERROR:", err, file=self.errf)
            if g_debug:
                print_exc(file=self.errf)
            return False

    def delete_file(self, path: Path) -> bool:
        print("deleting file", quoted_path(path), file=self.outf)
        try:
            shutil.unlink(path)
            return True
        except Exception as err:
            print("ERROR:", err, file=self.errf)
            if g_debug:
                print_exc(file=self.errf)
            return False

    def delete_dir(self, path: Path) -> bool:
        print("deleting directory", quoted_path(path), file=self.outf)
        try:
            shutil.rmtree(path)
            return True
        except Exception as err:
            print("ERROR:", err, file=self.errf)
            if g_debug:
                print_exc(file=self.errf)
            return False

    def make_symlink(self, link_path: Path, target_path: Path) -> bool:
        if link_path.is_relative_to(Path.home()) and \
                target_path.is_relative_to(Path.home()):
            target_path = Path(
                os.path.relpath(target_path, start=link_path.parent)
            )
        print(
            "placing symbolic link at", quoted_path(link_path),
            "to", quoted_path(target_path), file=self.outf
        )
        try:
            link_path.symlink_to(target_path)
            return True
        except Exception as err:
            print("ERROR:", err, file=self.errf)
            if g_debug:
                print_exc(file=self.errf)
            return False

    def require_dir(self, dir_path: Path):
        if not dir_path.exists():
            print("making directory:", dir_path, file=self.outf)
            dir_path.mkdir()


def from_command_line(args: Sequence[str] | None = None) -> Install:
    ap = argparse.ArgumentParser(
        description="""
            """
    )
    ap.add_argument(
        "-c", "--copy", action="store_true",
        help="""
            Normally, this script places symbolic links within the Application
            Support subdirectory, but with this option, it copies everything
            to that destination instead, making it self-contained. Note that
            once you have a copy, subsequent runs (even without this option)
            will continue to update the stored files after they have been
            modified."""
    )
    ap.add_argument(
        "project_path", nargs="*",
        help="""
            If you supply any extra project paths, these will get symlinked
            (or copied with -c) into the projects subdirectory. For example,
            a project directory called "foo" would give you
            "~/Library/Application Support/automator_util/proj/foo"
            (assuming default "config.json" settings).
            """
    )
    res = ap.parse_args(args)
    return Install(
        projects=[Path(p) for p in res.project_path],
        copy_mode=res.copy
    )


def quoted_path(path: Path) -> str:
    return shlex.quote(str(path))


if __name__ == "__main__":
    try:
        if not from_command_line().run():
            print("some errors were reported", file=sys.stderr)
            sys.exit(1)
    except Exception as err:
        print("ERROR:", err, file=sys.stderr)
        if g_debug:
            print_exc()
        sys.exit(3)
