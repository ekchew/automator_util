#!/usr/bin/env python3


"""
This script manages the directories automator_util sets up within
`~/Library/Application Support`. It can be run as a stand-alone command line
tool or imported as a module built around an `Install` class.

Globals:
    g_debug:
        When set True, any exceptions caught by this script or `uninstall.py`
        will include tracebacks. (Even when False, you will still see error
        messages printed to stderr.)

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
    """
    This class implements most of the `install.py` script's command line
    functionality. If you decide to import the script as a module instead,
    instatiate the class with suitable args and then call the `run` method.

    Attributes:
        projects: optional source paths to project directories you want to link
            Even if none are supplied, the `run` method will still set up the
            base directory withing `Application Support`.
        copy_mode: make copies rather than symlinking?
        outf, errf: `run` and other methods print progress to these streams
            They default to stdout and stderr, respectively.
    """
    projects: Sequence[Path] = field(default_factory=list)
    copy_mode: bool = False
    outf: tp.TextIO = sys.stdout
    errf: tp.TextIO = sys.stderr

    def run(self) -> bool:
        """
        This is the central method you want to call on an `Install` instance.
        It returns False if any non-fatal errors are encountered. (A fatal
        error would raise an Exception. This could happen, for example, if the
        script is unable to make an `automator_util` directory within
        `Application Support`.)
        """
        config = load_config(self.outf)
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
        """
        This method is called by `run` to make sure a source path is
        represented at its destination somewhere within `Application Support`
        by either a symlink or a full up-to-date copy.

        Args:
            src_path: an external path outside `Application Support`
                This must exist.
            dst_path: the corresponding path within `Application Support`
                This need not exist yet. If it does and is not a symlink, it
                must match the type of `src_path`. If `src_path` is a
                directory, `dst_path` had better be a directory also. Or they
                had both better be files.
            delete:
                This option is only relevant in copy mode when you are dealing
                with a directory. When set True, it will delete any items from
                the destination directory (if it exists) that cannot be found
                in the source. `run` does this automatically for project
                directories.
        """
        success = True

        # To begin with, we need to make sure the parent directory of the
        # destination exists. (This could be the `automator_util` or `proj`
        # directory, or even some nested subdirectory when syncing a project
        # in copy mode.)
        self.require_dir(dst_path.parent)

        if dst_path.exists():
            if dst_path.is_symlink():

                # In this case, we have found a symlink already occupying the
                # destination path. The only reason NOT to replace it is if it
                # still points to the new src_path and we are not in copy mode.
                try:
                    replace = self.copy_mode or not \
                        dst_path.resolve(strict=True).samefile(
                            src_path.resolve(strict=True))
                except Exception:
                    # An exception could be raised if either of the paths
                    # cannot be fully resolved and compared. In this case, we
                    # should replace the symlink regardless. It could, for
                    # example, be that the source directory had been moved and
                    # the symlink is now broken, in which case it is likely
                    # that this syncing operation is an attempt to repair it.
                    replace = True

                # To replace the link, we first delete it and then recursively
                # call `sync` again on the same paths to make a new link or
                # copy.
                if replace:
                    success = self.delete_file(dst_path) and \
                        self.sync(src_path, dst_path, delete)

            elif src_path.is_dir():

                # This is the most complex situation in which we are syncing
                # a directory which already exists. In this case, we need to
                # walk the directory tree and carefully examine what, if
                # anything, has changed.
                #
                # First obtain listings of both the source and destination
                # directories as Python sets for comparison purposes.
                src_set = set(src_path.iterdir())
                dst_set = set(dst_path.iterdir())

                # Walk the source directory set, syncing all items within.
                for subpath in src_set:
                    success = self.sync(
                        src_path=subpath,
                        dst_path=dst_path/subpath.name,
                        delete=delete
                    ) and success

                # If delete mode was specified, we need to remove all items in
                # the destination set that are not also in the source.
                if delete:
                    for subpath in dst_set - src_set:
                        if subpath.is_dir():
                            success = self.delete_dir(subpath) and success
                        else:
                            success = self.delete_file(subpath) and success

            else:

                # In comparing 2 files, we check to see if they are different
                # sizes or the source has been modified more recently than the
                # destination.
                src_stat = src_path.stat()
                dst_stat = dst_path.stat()
                if src_stat.st_size != dst_stat.st_size or \
                        src_stat.st_mtime > dst_stat.st_mtime:

                    # That being the case, we delete the destination and
                    # re-copy the source.
                    success = self.delete_file(dst_path) \
                        and self.copy_file(src_path, dst_path)

        # The remaining cases cover what to do when there is no destination
        # file or directory. We either copy or symlink the source to the
        # destination in that case.
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
            path.unlink()
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


def from_command_line(args: tp.Optional[Sequence[str]] = None) -> Install:
    ap = argparse.ArgumentParser(
        description="""
            Running this script makes sure everything is set up within the
            "~/Library/Application Support" directory. It prints progress to
            stdout and error messages to stderr. Error codes include: 1=some
            operation(s) failed, 2=script aborted on fatal exception."""
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
        sys.exit(2)
