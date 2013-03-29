from ..models import DBSession, Settings
from .helperlib import serialize_relation
from sqlalchemy.orm.exc import NoResultFound
import json

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
    
    def to_dict(self):
        return dict(DBSession.query(Settings.name, Settings.value))
    
    def from_dict(self, data):
        DBSession.query(Settings).delete()
        for k, v in data.items():
            DBSession.add(Settings(k, v))