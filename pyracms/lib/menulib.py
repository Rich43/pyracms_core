from ..models import DBSession, MenuGroup, Menu
from sqlalchemy.orm.exc import NoResultFound
from json import dumps
from pyracms.lib.helperlib import serialize_relation


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
                            permissions='', route_json={}):
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
        item.route_json = dumps(route_json)
        DBSession.add(item)
        return item

    def to_dict(self):
        output = {}
        groups = self.list_groups()
        for item in groups:
            output[item.name] = serialize_relation(item.menu_items)
        return output

    def from_dict(self, data):
        for k, v in data.items():
            try:
                group = self.show_group(k)
            except MenuGroupNotFound:
                group = MenuGroup(k)
                DBSession.add(group)
            for item in v:
                try:
                    DBSession.query(Menu).filter_by(id=item["id"]).one()
                except NoResultFound:
                    m = Menu(item["name"], item["type"], item["position"],
                             group, item["permissions"])
                    m.route_name = item["route_name"]
                    m.route_json = item["route_json"]
                    m.url = item["url"]
                    group.menu_items.append()
