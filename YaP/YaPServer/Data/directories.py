
import os

def create_directory_structure(server_dir):

    dirnames = ["logs",
                "configs",
                "users",
                "guistatic",
                "storage"
                ]
    dirs = {dn:os.path.join(server_dir, dn) for dn in dirnames}

    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    return dirs
