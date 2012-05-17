from sqlalchemy.orm.exc import NoResultFound
from ..models import DBSession, Settings

class SettingNotFound(Exception):
    pass

class SettingsLib():
    """
    A library to manage the settings database.
    """
    
    def list(self): #@ReservedAssignment
        """
        List all the settings
        """
        return DBSession.query(Settings.name, Settings.value)

    def update(self, name, value):
        """
        Update a page
        Raise PageNotFound if page does not exist
        """
        setting = self.show_setting(name)
        setting.value = value
        
    def show_setting(self, name):
        """
        Get setting object.
        Raise SettingNotFound if setting does not exist.
        """
        try:
            page = DBSession.query(Settings).filter_by(name=name).one()
        except NoResultFound:
            raise SettingNotFound
        return page
