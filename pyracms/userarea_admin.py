"""
Admin area module.
Add/Edit/Delete the menus, Add/Edit/Delete ACL Records.
"""
from .deform_schemas.userarea_admin import (EditMenuItems, 
                                                              MenuGroup, 
                                                              EditACL)
from .errwarninfo import * #@UnusedWildImport
from .models import Menu
from .lib.helperlib import (redirect, rapid_deform, 
                                                serialize_relation, 
                                                deserialize_relation)
from .lib.menulib import MenuLib
from pyramid.view import view_config
from pyramid.url import route_url

m = MenuLib()

@view_config(route_name='userarea_admin_edit_menu', permission='edit_menu', 
             renderer='list.jinja2')
def edit_menu(context, request):
    """
    Allow user to pick a menu group which is needed for editing items.
    See: edit_menu_item
    """
    message = "Menu Groups"
    route_name = "userarea_admin_edit_menu_item"
    return {'items': [(route_url(route_name, request, 
                                 group=item.name), item.name) 
                      for item in m.list_groups()],
            'title': message, 'header': message}

@view_config(route_name='userarea_admin_edit_menu_item', 
             permission='edit_menu', renderer='deform.jinja2')
def edit_menu_item(context, request):
    """
    Display form that lets you edit menu items from a specified group.
    See: edit_menu
    """
    def edit_menu_item_submit(context, request, deserialized, bind_params):
        """
        Save new list of menu items to database
        """
        group = bind_params["group"]
        group.menu_items = deserialize_relation(deserialized['menu'], Menu,
                                                {"group": group})
        request.session.flash(INFO_MENU_UPDATED % group.name, INFO)
        return redirect(request, 'userarea_admin_edit_menu')
    group = m.show_group(request.matchdict.get('group'))
    appstruct = {'menu': serialize_relation(group.menu_items)}
    result = rapid_deform(context, request, EditMenuItems, 
                          edit_menu_item_submit, appstruct=appstruct,
                          group=group)
    if isinstance(result, dict):
        message = "Editing " + group.name
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_edit_menu_group', 
             permission='edit_menu', renderer='deform.jinja2')
def edit_menu_group(context, request):
    """
    Display form that lets you edit menu groups
    """
    def edit_menu_group_submit(context, request, deserialized, bind_params):
        """
        Save new list of menu groups to database
        """
        groups = set([g.name for g in bind_params["groups"]])
        deserialized_groups = set(deserialized['menu_groups'])
        list(map(m.add_group, deserialized_groups - groups))
        list(map(m.delete_group, groups - deserialized_groups))
        request.session.flash(INFO_MENU_GROUP_UPDATED, INFO)
        return redirect(request, 'userarea_admin_edit_menu')
    groups = m.list_groups().all()
    appstruct = {'menu_groups': 
                 [x['name'] for x in serialize_relation(groups)]}
    result = rapid_deform(context, request, MenuGroup, 
                          edit_menu_group_submit, appstruct=appstruct,
                          groups=groups)
    if isinstance(result, dict):
        message = "Editing Menu Groups"
        result.update({"title": message, "header": message})
    return result

def dict_to_acl(item):
    """
    Convert (converted) dictionary ACL to normal tuple format
    """
    return (item['allow_deny'], item['who'], item['permission'])

def acl_to_dict(item):
    """
    Convert standard tuple ACL format to a dictionary
    """
    return {'allow_deny': item[0], 'who': item[1], 'permission': item[2]}

@view_config(route_name='userarea_admin_edit_acl', 
             permission='edit_acl', renderer='deform.jinja2')
def edit_acl(context, request):
    """
    Display a form that lets you edit the access control list
    """
    def edit_acl_submit(context, request, deserialized, bind_params):
        """
        Save new access control list to database
        """
        context.__acl__ = set(map(dict_to_acl, deserialized['acl']))
        context.sync_to_database()
        request.session.flash(INFO_ACL_UPDATED, INFO)
        return redirect(request, 'home')
    appstruct = {'acl': list(map(acl_to_dict, context.__acl__))}
    result = rapid_deform(context, request, EditACL, 
                          edit_acl_submit, appstruct=appstruct)
    if isinstance(result, dict):
        message = "Editing Access Control List"
        result.update({"title": message, "header": message})
    return result