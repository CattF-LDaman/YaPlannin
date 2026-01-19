from YaP.YaPCore.Data.datafile import Datafile
from YaP.YaPCore.Data.datatypes import D_RAW,D_INT64,D_BOOL
from YaP.YaPCore.Data.hashing import hash_pwd, hash_str

import os
import time

class UserDataStorage:

    def __init__(self, location):

        self.location = location

    def exists(self, username):
        return UserData(self.location, username).exists

    def load(self, username):
        udata = UserData(self.location, username)
        if not udata.exists:
            raise ValueError(f"User {username} does not exist.")
        return udata
    
    def load_all(self):
        
        return [UserData(self.location, dfilename.split(".")[0]) for dfilename in os.listdir(self.location)]

    def new(self, username, password):
        for char in username:
            if char.upper() not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_":
                raise ValueError("Usernames can only contain alphanumerics and underscores.")
        if len(username) > 32:
            raise ValueError("Usernames can be at most 32 characters long.")
        udata = UserData(self.location, username)
        udata.create(password)

class UserData(Datafile):

    DATA_VERSION = 4
    STRUC = (
            ("pwd_hash", D_RAW, 1),
            ("salt", D_RAW, 1),
            ("created", D_INT64),
            ("last_login", D_INT64),
            ("last_write", D_INT64),
            )


    def __init__(self, users_dir, username):

        self.username = username
        self.user_hash = hash_str(username)

        super().__init__(os.path.join(users_dir, self.user_hash+'.user'))
    
    def on_create(self, new_pwd):

        self.change_password(new_pwd)
        self.last_login = 0
        self.created = int(time.time())

    def on_save(self):

        self.last_write = int(time.time())

    def check_password(self, pwd):
        
        pwd_h = hash_pwd(pwd.encode('utf-8'), self.salt)

        return pwd_h == self.pwd_hash
    
    def login(self):

        self.last_login = int(time.time())
        self.save()

    def change_password(self, pwd):

        self.salt = os.urandom(16)
        self.pwd_hash = hash_pwd(pwd.encode('utf-8'), self.salt)

        if self.exists:
            self.save()
