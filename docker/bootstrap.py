import os
import sys

from YaP.YaPServer.Data.directories import create_directory_structure
from YaP.YaPServer.Data.userdata import UserDataStorage


def main() -> int:
    username = os.environ.get("YAP_BOOTSTRAP_USER")
    password = os.environ.get("YAP_BOOTSTRAP_PASSWORD")
    if not username or not password:
        return 0

    data_dir = os.environ.get("YAP_DATA_DIR", "/data/YaPServer")
    dirs = create_directory_structure(data_dir)
    uds = UserDataStorage(dirs["users"])

    if uds.exists(username):
        print(f"Bootstrap user '{username}' already exists, skipping.")
        return 0

    uds.new(username, password)
    print(f"Bootstrap user '{username}' created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
