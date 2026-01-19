
from YaP.YaPCore.Data.struc import build_struc, read_struc

import os

class Datafile:

    DATA_VERSION = 1
    AUTO_CREATE = False
    STRUC = ()

    def __init__(self, location):

        self.location = location

        for dataname, *_, in self.STRUC:
            setattr(self, dataname, None)

        if not self.exists and self.AUTO_CREATE:
            self.create()

        if self.exists:
            self.read()

    @property
    def exists(self):
        return os.path.exists(self.location)
    
    def create(self, *args, **kwargs):  # All datapieces should have a value albeit a default one
        
        self.on_create(*args, **kwargs)
        self.reload()

    def reload(self):

        self.save()
        self.read()

    def on_save(self):
        pass

    def on_create(self):
        pass

    def on_read(self):
        pass

    def save(self):

        self.on_save()

        fdata = {dataname:getattr(self,dataname) for dataname, *_ in self.STRUC}

        fdata_packed = build_struc(self.STRUC, fdata)

        with open(self.location, 'wb') as uf:
            uf.write(self.DATA_VERSION.to_bytes(1,"little"))
            uf.write(fdata_packed)

    def read(self):

        if not self.exists:
            return False

        self.on_read()

        with open(self.location, 'rb') as df:

            df_version = df.read(1)[0]
            if df_version != self.DATA_VERSION:
                raise ValueError(f"DF version missmatch: {df_version} != {self.DATA_VERSION}")
            
            udata = read_struc(self.STRUC, df.read())
            for k,v in udata.__dict__.items():
                setattr(self, k, v)
        
        return True

    def delete(self):

        os.remove(self.location)