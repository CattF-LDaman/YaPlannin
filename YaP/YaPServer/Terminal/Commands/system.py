from YaP.YaPCore import VERSION_STRING, BUILD

import time
import os
import json

def stop(server, args):
    """Stop server, nicely."""
    time.sleep(0.5)
    server.close()

def reloadconf(server, args):
    """DEPRECATED: Reloads config from files."""
    server.config.load()
    server.logger.config = server.config.logging.__dict__

    return "Config reloaded. WARNING: Some changes might still require restart to take effect."

def version(server, args):
    """Shows version and build of running server."""

    return f"Shinezumi RAT\nVersion: {VERSION_STRING}\nBuild: {BUILD}"

# def banhost(server, args):
#     """Bans IP from accessing GUI."""
#     with open(os.path.join(server.dirs["configs"], "banned.json"), "r") as banned_f:
#         bf = json.load(banned_f)

#     if args[0] in bf["banned_usernames"]:
#         return f"Failed: username '{args[0]}' was already banned."
#     bf["banned_usernames"].append(args[0])

#     with open(os.path.join(server.dirs["configs"], "banned.json"), "w") as banned_f:
#         json.dump(bf, banned_f)

#     return f"Username '{args[0]}' has been banned."

# def pardonhost(server, args):
#     """Unbans IP from accessing GUI"""
#     with open(os.path.join(server.dirs["configs"], "banned.json"), "r") as banned_f:
#         bf = json.load(banned_f)

#     if args[0] not in bf["banned_usernames"]:
#         return f"Failed: username '{args[0]}' was not banned."
#     bf["banned_usernames"].remove(args[0])

#     with open(os.path.join(server.dirs["configs"], "banned.json"), "w") as banned_f:
#         json.dump(bf, banned_f)

#     return f"Username '{args[0]}' has been unbanned."

# def bannedhosts(server, args):
#     """Shows what IPs are banned."""
#     with open(os.path.join(server.dirs["configs"], "banned.json"), "r") as banned_f:
#         banned = json.load(banned_f)["banned_usernames"]
#     return ", ".join(banned)