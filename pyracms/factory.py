from .lib.settingslib import SettingsLib, SettingNotFound
from .models import DBSession
from collections import UserList
import json

def save(obj):
    hashable = tuple([tuple(x) for x in obj])
    obj.json = json.dumps(list(set(hashable)), indent=4)
    try:
        obj.settings.update("ACL", obj.json)
    except SettingNotFound:
        obj.settings.create("ACL", obj.json)

class JsonList(UserList):
    def __init__(self, *args, **kwargs):
        session = None
        try:
            session = kwargs['session']
            del(kwargs['session'])
        except KeyError:
            pass
        self.settings = SettingsLib(session)
        if args:
            super().__init__(*args, **kwargs)
            save(self)
        else:
            try:
                db_data = self.settings.show_setting("ACL")
                super().__init__(json.loads(db_data))
            except SettingNotFound:
                super().__init__()
                save(self)
            
    def __getattribute__(self,name):
        attr = super(UserList, self).__getattribute__(name)
        if hasattr(attr, '__call__'):
            def newfunc(*args, **kwargs):
                result = attr(*args, **kwargs)
                save(self)
                return result
            return newfunc
        else:
            return attr

class RootFactory(object):
    """
    Default context for views.
    """
    
    def __init__(self, request=None, session=None):
        self.request = request
        if session:
            self.__acl__ = JsonList(session=session)
        else:
            self.__acl__ = JsonList(session=DBSession)