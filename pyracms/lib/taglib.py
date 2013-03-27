import string

ARTICLE = "page"
GAMEDEP = "game"
BOARD = "thread"

class InvalidTagType(Exception):
    pass

class AlreadyVoted(Exception):
    pass

class TagLib():
    """
    A library to get and set tags to/from database.
    Also handles votes (To save code!)
    """
    
    def __init__(self, cls, tag_type):
        if not tag_type in [ARTICLE, GAMEDEP, BOARD]:
            raise InvalidTagType
        self.tag_type = tag_type
        self.cls = cls
        
    def filter_tags(self, tags):
        """
        Convert command seperated list to a list
        """
        result = []
        charset = string.ascii_letters + string.digits + "-_"
        for tag in tags.split(","):
            tag = "".join([c for c in tag if c in charset])
            tag = tag.strip().lower()
            result.append(tag)
        return list(set(result))

    def format_tags(self, tag_result):
        """
        Convert list to command seperated list
        """
        return ",".join(t.name for t in tag_result)

    def get_tags(self, db_obj):
        """
        Return an objects tags as a comma seperated list
        """
        if not db_obj:
            return ''
        return self.format_tags(db_obj.tags)

    def set_tags(self, db_obj, tags):
        """
        Give an object some new tags from comma seperated list
        """
        # Filter junk out of user input
        tags = self.filter_tags(tags)

        # Remove all tags in database
        db_obj.tags = []

        # Add new set of tags
        for tag in tags:
            db_tag = self.cls(tag)
            setattr(db_tag, self.tag_type, db_obj)
            db_obj.tags.append(db_tag)
