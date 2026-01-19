
import os
import json
from types import SimpleNamespace

# General class for handling config files
class Config:

    def __init__(self, location, defaults={}):

        self.defaults = defaults

        self.path = location

        self.create_config_structure()
        self.load()

    def get_config_filepath(self,conf_type: str):
        return os.path.join(self.path, conf_type+".json")

    def create_config_structure(self):

        for conf_type, conf in self.defaults.items():

            conf_path = self.get_config_filepath(conf_type)

            if not os.path.exists(conf_path):

                with open(conf_path, "w") as cf:

                    json.dump(conf, cf, indent=4)

    def load(self):

        for conf_type, default_conf in self.defaults.items():

            conf_path = self.get_config_filepath(conf_type)

            with open(conf_path, "r") as cf:
                conf = {**default_conf, **json.load(cf)}

            setattr(self, conf_type, SimpleNamespace(**conf))