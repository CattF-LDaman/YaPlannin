import os

from YaP.YaPServer.server import Server

if __name__ in ["__main__", "__mp_main__"]:
    kwargs = {}
    if data_dir := os.environ.get("YAP_DATA_DIR"):
        kwargs["server_directory"] = data_dir
    Server(**kwargs).run()