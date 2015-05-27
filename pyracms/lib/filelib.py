from pyramid.path import AssetResolver
from pyracms.models import DBSession, Files
from uuid import uuid1
from os.path import join, split, splitext
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

    def open_media(self, filename):
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from PIL import Image

        is_image = False
        is_video = False
        media_obj = None
        try:
            media_obj = Image.open(filename)
            is_image = True
        except OSError:
            is_image = False
            try:
                media_obj = VideoFileClip(filename)
                is_video = True
            except OSError:
                pass
            except AttributeError:
                pass
        return (is_image, is_video, media_obj)

    def write(self, filename, file_obj, mimetype, thumbnail=False,
              thumbnail_size=(256, 256)):
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
        if thumbnail:
            from PIL import Image
            is_image, is_video, media_obj = self.open_media(name_with_path)
            str_file, ext = splitext(name_with_path)
            if is_image:
                media_obj.thumbnail(thumbnail_size)
                media_obj.save(str_file + ".thumbnail.png", "png")
            if is_video:
                main_path = str_file + ".main.png"
                media_obj.save_frame(main_path, media_obj.duration/10)
                im_obj = Image.open(main_path)
                im_obj.thumbnail(thumbnail_size)
                im_obj.save(str_file + ".thumbnail.png", "png")
            if not is_image and not is_video:
                return f
        f.upload_complete = True
        return f

    def delete(self, db_file):
        DBSession.flush()
        path = join(self.get_static_path(), self.UPLOAD_DIR, 
                    db_file.uuid)
        rmtree(path, True)
        DBSession.delete(db_file)
