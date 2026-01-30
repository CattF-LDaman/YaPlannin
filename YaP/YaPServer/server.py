
from YaP.YaPCore.version import VERSION_STRING
from YaP.YaPCore.Data import get_data_dir
from YaP.YaPCore.Data.logging import Logger
from YaP.YaPCore.Data.config import Config

from YaP.YaPServer.Terminal.terminal import Terminal
from YaP.YaPServer.GUI import GUI
from YaP.YaPServer.Data.directories import create_directory_structure
from YaP.YaPServer.Data.config import DEFAULT_CONFIG
from YaP.YaPServer.Data.userdata import UserDataStorage
from YaP.YaPServer.Data.database import YaPDB

import os
import sys
import time

class Server:

    def __init__(self, server_directory=get_data_dir("YaPServer"), bundled=False):

        self.server_directory = server_directory
        self.bundled = bundled # Whether server is an executable

        self.session_id = os.urandom(4)
        self.start_time = time.time()

        self.dirs = create_directory_structure(self.server_directory)

        self.config = Config(self.dirs["configs"], DEFAULT_CONFIG)

        self.log_file_path = os.path.join(self.dirs["logs"], f"YaPServer_{self.session_id.hex()}_{int(self.start_time)}.log")
        self.logger = Logger(self.log_file_path, self.config.logging)
        self.log = self.logger.log
        print(f"Logs for current session can be found at ' {self.log_file_path} ''")

        self.log(f"{self.config.server.title} with version {VERSION_STRING} on {sys.platform}", 10)

        self.user_data_storage = self.uds = UserDataStorage(self.dirs["users"])
        self.database = YaPDB(self)

        self.terminal = Terminal(self)
        self.gui = GUI(self)

        self.log("Server initialised.")

    def close(self,exit_code=0):

        if exit_code == 0:
            self.log("Server closed.")
        else:
            self.log(f"Server closed with exit code {exit_code}")

        self.terminal.running = False

        self.logger.close()

        sys.exit(exit_code)

    def run(self):

        self.log("Server starting...")

        self.terminal.run()
        self.gui.start()
