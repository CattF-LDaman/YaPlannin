
from .system import stop, reloadconf, version#, banhost, pardonhost, bannedhosts
from .auth import createuser, removeuser, changepass

import os
import inspect

all_cmds = [stop,
            reloadconf, 
            version, 

            #banhost, pardonhost, bannedhosts,

            createuser, removeuser, changepass,
        ]

redacted_argument_logging = [createuser, changepass]

commands = {cmd.__name__:cmd for cmd in all_cmds}

alias = {"exit":"stop", "?":"help",
         "build":"version", "unbanhost": "pardonhost",
         "cuser": "createuser", "ruser":"removeuser", "remuser": "removeuser", "cpass": "changepass", "changeuser": "changepass"}

commands["listcmds"] = lambda s,a : f"All commands:\n{os.linesep.join(sorted(list(commands)))}"
commands["help"] = lambda s,a : f"All commands:\n\n{os.linesep.join([f'{cmdn}: {inspect.getdoc(command)}' if inspect.getdoc(command) else f'{cmdn}: No description.' for cmdn,command in sorted(commands.items())])}"