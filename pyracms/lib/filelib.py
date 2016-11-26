from datetime import datetime

from pyramid.path import AssetResolver
from pyracms.models import DBSession, Files, APIFileUpload
from uuid import uuid1
from os.path import join, splitext
from os import mkdir
from time import time
from shutil import rmtree

from sqlalchemy.orm.exc import NoResultFound

resolve = AssetResolver().resolve

class APIFileNotFound(Exception):
    pass

class FileLib:
    UPLOAD_DIR = "uploads"

    def __init__(self, request):
        self.request = request

    def filename_filter(self, filename):
        return "".join(filter(lambda c: c.isalnum() or c in [".", "_"],
                              filename))

    def get_filename(self, filename):
        uuid = str(uuid1(clock_seq=int(time())))
        return (uuid, join(uuid, filename))

    def get_static_path(self):
        setting_data = self.request.registry.settings.get("static_path")
        return resolve(setting_data).abspath()

    def open_media(self, filename):
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
                from moviepy.video.io.VideoFileClip import VideoFileClip
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
        Make a new File record.
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
                f.is_picture = True
            if is_video:
                main_path = str_file + ".main.png"
                media_obj.save_frame(main_path, media_obj.duration/10)
                im_obj = Image.open(main_path)
                im_obj.thumbnail(thumbnail_size)
                im_obj.save(str_file + ".thumbnail.png", "png")
                f.is_video = True
                f.video_duration = media_obj.duration
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

    def api_show(self, api_uuid):
        """
        Find a APIFileUpload object in database.
        :param api_uuid: uuid of uploaded file
        :return: APIFileUpload object
        """
        try:
            file_obj = DBSession.query(APIFileUpload).filter_by(
                name=api_uuid).one()
        except NoResultFound:
            raise APIFileNotFound
        return file_obj

    def api_write(self, filename, file_obj, mimetype):
        """
        Upload a file using Pyracms API
        :param filename: Filename from uploaded file
        :param file_obj: Standard Python File object from uploaded file
        :param mimetype: Uploaded files mimetype
        :return: APIFileUpload object
        """
        f = self.write(filename, file_obj, mimetype, True)
        DBSession.flush()
        file_upload_obj = APIFileUpload(f)
        DBSession.add(file_upload_obj)
        DBSession.flush()
        return file_upload_obj

    def api_delete(self, api_uuid):
        api_obj = self.api_show(api_uuid)
        path = join(self.get_static_path(), self.UPLOAD_DIR,
                    api_obj.file_obj.uuid)
        rmtree(path, True)
        DBSession.delete(api_obj)

    def api_delete_expired(self):
        """
        Delete all expired API File Upload objects
        """
        now = datetime.now()
        for item in DBSession.query(APIFileUpload).filter(
                        APIFileUpload.expires <= now):
            self.api_delete(item.name)