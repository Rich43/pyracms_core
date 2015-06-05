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
        group = MenuGroup(name)
        DBSession.add(group)
        return group
        
    def delete_group(self, name):
        """
        Delete menu group by name
        """
        DBSession.delete(self.show_group(name))

    def add_menu_item_url(self, name, url, position, group, permissions=''):
        """
        Add a menu item with a custom url
        :param name: Name of menu item
        :param url: URL of menu item
        :param position: Position in list
        :param group: Menu Group it belongs to
        :param permissions: Permissions for the item
        :return:
        """
        item = Menu(name, "url", position, group, permissions)
        item.url = url
        DBSession.add(item)
        return item

    def add_menu_item_route(self, name, route_name, position, group,
                            permissions=''):
        """
        Add a menu item with a route
        :param name: Name of menu item
        :param route_name: Name of route
        :param position: Position in list
        :param group: Menu Group it belongs to
        :param permissions: Permissions for the item
        :return:
        """
        item = Menu(name, "route", position, group, permissions)
        item.route_name = route_name
        DBSession.add(item)
        return item