
import os


DEFAULT_CONFIG = {
    "server": {
        "title": "YaPlannin"
    },

    "logging": {
        "print_logs":True,
        "write_logs":True,
        "print_logs_from_level":2,
        "write_logs_from_level":0
    },

    "gui": {
        "primary_color":"#99f",
        "action_color":"#33f"
    },

    "banned": {
        "banned_hosts": []
    },

    "secret": {
        "browser_storage_secret": os.urandom(32).hex()
    },
}