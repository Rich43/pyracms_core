from ..models import DBSession, MenuGroup, Menu
from .helperlib import serialize_relation
from sqlalchemy.orm.exc import NoResultFound

class MenuGroupNotFound(Exception):
    pass

class MenuLib():
    """
    A library to manage menus
    """
    
    def show_group(self, name):
        """
        Get menu group database object, filtered by name
        """
        try:
            return DBSession.query(MenuGroup).filter_by(name=name).one()
        except NoResultFound:
            raise MenuGroupNotFound(name)
        
    def list_groups(self):
        """
        List menu groups
        """
        return DBSession.query(MenuGroup)
    
    def add_group(self, name):
        """
        Add menu grop
        """
        DBSession.add(MenuGroup(name))
        
    def delete_group(self, name):
        """
        Delete menu group by name
        """
        DBSession.delete(self.show_group(name))
    
    def to_dict(self):
        output = {}
        groups = self.list_groups()
        for item in groups:
            output[item.name] = serialize_relation(item.menu_items)
        return output
    
    def from_dict(self, data):
        DBSession.query(MenuGroup).delete()
        DBSession.query(Menu).delete()
        for k, v in data.items():
            group = MenuGroup(k)
            for item in v:
                group.menu_items.append(Menu(item["name"], item["url"], 
                                             item["position"], group, 
                                             item["permissions"]))
            DBSession.add(group)