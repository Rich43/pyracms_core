from ..models import DBSession, Settings
from sqlalchemy.orm.exc import NoResultFound

class SettingNotFound(Exception):
    pass

class SettingsLib():
    """
    A library to manage the settings database.
    """
    def __init__(self, session=None):
        if session:
            self.DBSession = session
        else:
            self.DBSession = DBSession
            
    def list(self): #@ReservedAssignment
        """
        List all the settings
        """
        return self.DBSession.query(Settings.name, Settings.value)

    def create(self, name, value):
        """
        Update a page
        Raise PageNotFound if page does not exist
        """
        self.DBSession.add(Settings(name, value))

    def update(self, name, value):
        """
        Update a page
        Raise PageNotFound if page does not exist
        """
        setting = self.show_setting(name)
        setting.value = value
        
    def show_setting(self, name, as_obj=False):
        """
        Get setting object.
        Raise SettingNotFound if setting does not exist.
        """
        try:
            page = self.DBSession.query(Settings).filter_by(name=name).one()
        except NoResultFound:
            raise SettingNotFound
        if as_obj:
            return page
        else:
            return page.value
    
    def to_dict(self):
        return dict(self.DBSession.query(Settings.name, Settings.value))
    
    def from_dict(self, data):
        self.DBSession.query(Settings).delete()
        for k, v in data.items():
            self.DBSession.add(Settings(k, v))