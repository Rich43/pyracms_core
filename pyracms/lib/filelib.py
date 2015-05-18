from pyramid.path import AssetResolver
from pyracms.models import DBSession, Files
from uuid import uuid1
from os.path import join, split, samefile
from os import mkdir
from time import time
from shutil import rmtree
resolve = AssetResolver().resolve

class FileLib:
    UPLOAD_DIR = "uploads"

    def __init__(self, request):
        self.request = request

    def filename_filter(self, filename):
        return "".join(filter(lambda c: c.isalnum() or ".", filename))

    def get_filename(self, filename):
        uuid = str(uuid1(clock_seq=int(time())))
        return (uuid, join(uuid, filename))

    def get_static_path(self):
        setting_data = self.request.registry.settings.get("static_path")
        return resolve(setting_data).abspath()

    def write(self, filename, file_obj, mimetype):
        """
        Make a new File record, make needed
        FileData record(s) while reading data from self.fle,
        return the File record.
        """
        filename = self.filename_filter(filename)
        uuid, new_filename = self.get_filename(filename)
        name_with_path = join(self.get_static_path(), self.UPLOAD_DIR, 
                              new_filename)
        f = Files(filename, mimetype)
        f.uuid = uuid
        file_obj.seek(0,2)
        f.size = file_obj.tell()
        file_obj.seek(0)
        DBSession.add(f)
        try:
            mkdir(join(self.get_static_path(), self.UPLOAD_DIR))
        except OSError:
            pass
        try:
            mkdir(join(self.get_static_path(), self.UPLOAD_DIR, uuid))
        except OSError:
            pass
        file_out_obj = open(name_with_path, "wb")
        while True:
            buf = file_obj.read(10**6)
            if buf:
                file_out_obj.write(buf)
            else:
                break
        file_out_obj.close()
        f.upload_complete = True
        return f

    def delete(self, db_file):
        path = join(self.get_static_path(), self.UPLOAD_DIR, 
                    db_file.uuid)
        if not samefile(join(self.get_static_path(), self.UPLOAD_DIR),
                        path):
            rmtree(path, True)
            DBSession.delete(db_file)
