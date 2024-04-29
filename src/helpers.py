import json
import os
from contextlib import contextmanager

from constants import ROOT_DIR


@contextmanager
def open_project_file(name, *args, **kwargs):
    file_path = os.path.join(ROOT_DIR, name)
    with open(file_path, *args, **kwargs) as file:
        yield file


def load_config_file(name):
    with open_project_file(name, "r") as file:
        config_content = file.read()

    return json.loads(config_content)
