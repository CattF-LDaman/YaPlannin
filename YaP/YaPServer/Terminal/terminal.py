
from .Commands import commands, alias, redacted_argument_logging

from YaP.YaPCore.threading import threaded_daemon

import traceback

class Terminal:

    def __init__(self,server):

        self.server = server
        self.running = True

    def parse(self, cmd_in):

        cmd_in = cmd_in.strip()

        cmd = cmd_in.split(" ")[0]
        args = cmd_in.split(" ")[1:]

        if cmd in commands or cmd in alias:

            try:
                cmd_func = commands[alias[cmd] if cmd in alias else cmd]
                    
                self.server.log(f"CMD: {cmd}" + (" ".join(args) if cmd_func not in redacted_argument_logging else "<REDACTED>"))

                out = cmd_func(self.server, args)

                if out:
                    self.server.log(f"OUT:\n{out}\n")

            except Exception as e:

                self.server.log(f"Server encountered an error while executing your command:\n{''.join(traceback.format_exception(e, value=e ,tb=e.__traceback__))}",4)
        
        else:
            self.server.log(f"Unknown command: {cmd_in}",3)

    @threaded_daemon
    def run(self):

        self.server.log("You can now input commands.")
        while self.running:

            cmd_in = input()

            if self.running:
                self.parse(cmd_in)