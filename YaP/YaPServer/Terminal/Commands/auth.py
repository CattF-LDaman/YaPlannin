
def createuser(server, args):
    """Create a user to access GUI. Username can not contain spaces nor any character other than alphanumerics and underscores. Password can contain spaces and other characters. usage: createuser <USERNAME> <PASSWORD> """
    server.uds.new(args[0], " ".join(args[1:]))
    return f"User '{args[0]}' created."

def removeuser(server, args):
    """Remove GUI user. usage: remuser <USERNAME>"""
    server.uds.load(args[0]).delete()
    return "User removed."

def changepass(server, args):
    """Change GUI user password. usage: changepass <USERNAME> <PASSWORD> """
    server.uds.load(args[0]).change_password(" ".join(args[1:]))
    return f"User '{args[0]}' changed."