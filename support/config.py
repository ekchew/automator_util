from dataclasses import dataclass
import json
from pathlib import Path
import sys
import typing as tp


"""
This module manages anything read from the `config.json` file located at the
root level of this project.

As it stands, the only things you can configure are the names of the
directories created within `Application Support`. These default to
"automator_util" and "proj" in the absence of a config.

Globals: k_app_sup_dir_key, k_proj_dir_key
    These are the keys used to look up the directory names in `config.json`.

Requires: Python 3.7 or later (for dataclasses)
"""


k_app_sup_dir_key: tp.Final[str] = "Application Support Subdirectory"
k_proj_dir_key: tp.Final[str] = "Projects Subdirectory"


@dataclass
class Config:
    """
    Aside from storing the directory names, this class also defines 2 read-only
    properties that give you the full paths to the directories.
    """

    app_sup_dir_name: str = "automator_util"
    proj_dir_name: str = "proj"

    @property
    def app_sup_dir(self) -> Path:
        base_dir = Path.home()/"Library"/"Application Support"
        return base_dir/self.app_sup_dir_name

    @property
    def proj_dir(self) -> Path:
        return self.app_sup_dir/self.proj_dir_name


def load_config(outf: tp.TextIO = sys.stdout) -> Config:
    """
    This is the function that loads the `config.json` file (if present) and
    builds a `Config` instance out of it. It assumes the file would be 1 level
    outside its parent `support` directory.
    """
    config = Config()
    path = Path(__file__).parents[1]/"config.json"
    if path.exists():
        print("loading config file:", path, file=outf)
        with open(path, encoding="utf-8") as fp:
            obj: dict = json.load(fp)
        if asdn := obj.get(k_app_sup_dir_key):
            config.app_sup_dir_name = asdn
        if pdn := obj.get(k_proj_dir_key):
            config.proj_dir_name = pdn
    return config
