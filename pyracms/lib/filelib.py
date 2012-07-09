from ..models import Files, FilesData

class AlchemyIO:
    """class AlchemyIO
    Read and write files to the database.
    Takes in:
    1) file object          -   only needed for write
    2) a Files object that
       has been added and
       commited to the
       session.             -   only needed for read
    3) the session itself   -   only needed for write
    """
    def __init__(self, fle=None, sess=None, FilesObj=None, 
                 mime=None, filename=None):
        self.sess = sess
        self.FilesObj = FilesObj
        self.fle = fle
        self.mime = mime
        self.filename = filename
        
    def read(self):
        """
        Read data from FilesObj and yield it in
        1MB chunks.
        """
        if not self.FilesObj:
            raise Exception("FilesObj attribute is not set.")
        for item in self.FilesObj.data:
            yield item.data

    def read_from(self, pos):
        """
        Todo: Add ability to read, starting from a position.
        """
        pass

    def write(self):
        """
        Make a new File record, make needed
        FileData record(s) while reading data from self.fle,
        return the File record.
        """
        if not self.fle:
            raise Exception("fle attribute is not set.")
        if not self.sess:
            raise Exception("sess attribute is not set.")
        if not self.mime:
            raise Exception("mime attribute is not set.")
        if not self.filename:
            raise Exception("filename attribute is not set.")
        f = Files(self.filename, self.mime)
        self.fle.seek(0,2)
        f.size = self.fle.tell()
        self.fle.seek(0)
        self.sess.add(f)
        #transaction.commit()
        while True:
            buf = self.fle.read(10**6)
            if buf:
                fd = FilesData(buf)
                f.data.append(fd)
                #transaction.commit()
            else:
                break
        f.upload_complete = True
        return f

    def get_size(self):
        """
        Read data from FilesObj and
        get file size.
        """
        if not self.FilesObj:
            raise Exception("FilesObj attribute is not set.")
        size = 0
        for item in self.FilesObj.data:
            size += len(item.data)
        return size
