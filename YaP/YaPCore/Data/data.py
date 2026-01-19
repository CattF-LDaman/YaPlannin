
import sys
from os import getenv
from pathlib import Path


def get_data_dir(dirname):
    # Found: https://stackoverflow.com/questions/19078969/python-getting-appdata-folder-in-a-cross-platform-way #
    if sys.platform.startswith("win"):
        os_path = getenv("LOCALAPPDATA")
    elif sys.platform.startswith("darwin"):
        os_path = "~/Library/Application Support"
    else:
        # assume linux
        os_path = getenv("XDG_DATA_HOME", "~/.local/share")

    return Path(os_path).expanduser() / dirname