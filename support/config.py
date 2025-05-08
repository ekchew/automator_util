from dataclasses import dataclass
import json
from pathlib import Path
import typing as tp


k_app_sup_dir_key: tp.Final[str] = "Application Support Subdirectory"
k_proj_dir_key: tp.Final[str] = "Projects Subdirectory"


@dataclass
class Config:
    app_sup_dir_name: str = "automator_util"
    proj_dir_name: str = "proj"

    @property
    def app_sup_dir(self) -> Path:
        base_dir = Path.home()/"Library"/"Application Support"
        return base_dir/self.app_sup_dir_name

    @property
    def proj_dir(self) -> Path:
        return self.app_sup_dir/self.proj_dir_name


def load_config() -> Config:
    config = Config()
    path = Path(__file__).parents[1]/"config.json"
    if path.exists():
        with open(path, encoding="utf-8") as fp:
            obj: dict = json.load(fp)
        if asdn := obj.get(k_app_sup_dir_key):
            config.app_sup_dir_name = asdn
        if pdn := obj.get(k_proj_dir_key):
            config.proj_dir_name = pdn
    return config
