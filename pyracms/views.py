from .deform_schemas.userarea import (LoginSchema, RegisterSchema, 
    ChangePasswordSchema, RecoverPasswordSchema, EditUserSchema)
from .deform_schemas.userarea_admin import (EditACL, MenuGroup, EditMenuItems, 
    SettingSchema, RestoreSettingsSchema, EditAdminUserSchema)
from .factory import JsonList
from .lib.helperlib import (acl_to_dict, dict_to_acl, serialize_relation, 
    deserialize_relation, redirect, rapid_deform)
from .lib.menulib import MenuLib
from .lib.searchlib import SearchLib
from .lib.settingslib import SettingsLib
from .lib.tokenlib import TokenLib, InvalidToken
from .lib.userlib import UserLib
from .models import Menu
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.path import AssetResolver
from pyramid.response import Response
from pyramid.security import remember, forget, authenticated_userid
from pyramid.url import route_url
from pyramid.view import view_config
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from string import Template
import json
import os
import shutil
import transaction

u = UserLib()
t = TokenLib()
s = SettingsLib()
resolve = AssetResolver().resolve
ERROR = 'error'
WARN = 'warn'
INFO = 'info'

def dummy_home(context, request):
    return {}

@view_config(route_name='token_get')
def token_get(context, request):
    """
    Get a token, take action on it depending on its purpose
    """
    try:
        token = t.get_token(request.matchdict.get("token"))
        if token.purpose.name == "register":
            token.user.banned = False
            request.session.flash(s.show_setting("INFO_ACC_CREATED"), INFO)
            return redirect(request, "userarea_login")
    except InvalidToken:
        request.session.flash(s.show_setting("ERROR_TOKEN"), ERROR)
    return redirect(request, "home")

@view_config(route_name='search', renderer='search.jinja2')
def search(context, request):
    """
    Handle search queries
    """
    s = SearchLib()
    return {"items": s.search(request.matchdict['query'])}

@view_config(route_name='css')
def css(request):
    css_data = s.show_setting("CSS")
    return Response(app_iter=[css_data.encode()],
                    headerlist=[('Content-Type', "text/css"),
                                ('Content-Length', str(len(css_data)))])

@view_config(route_name='redirect_one')
@view_config(route_name='redirect_two')
def redirect_view(article, request):
    route_name = request.matchdict.get('route_name')
    gamedeptype = request.matchdict.get('type')
    return HTTPFound(location=route_url(route_name,
                                        request, type=gamedeptype,
                                        **request.POST))

@view_config(route_name='userarea_login', renderer='userarea/login.jinja2')
def userarea_login(context, request):
    """
    Display login form
    """
    def login_submit(context, request, deserialized, bind_params):
        """
        Submit login form
        """
        username = deserialized.get("username")
        password = deserialized.get("password")
        if u.login(username, password):
            headers = remember(request, username)
            request.session.flash(s.show_setting("INFO_LOGIN"), INFO)
            return HTTPFound(location=deserialized.get("redirect_url"),
                             headers=headers)
        else:
            request.session.flash(s.show_setting("ERROR_INVALID_USER_PASS"), 
                                  ERROR)
            return redirect(request, "userarea_login")
    if request.matched_route.name == "userarea_login":
        redirect_url = route_url("home", request)
    else:
        redirect_url = request.url
    return rapid_deform(context, request, LoginSchema, login_submit,
                        redirect_url=redirect_url)

@view_config(route_name='userarea_profile', renderer='userarea/profile.jinja2')
@view_config(route_name='userarea_profile_two', 
             renderer='userarea/profile.jinja2')
def userarea_profile(context, request):
    """
    Display either current or specified user's profile
    """
    user = request.matchdict.get('user') or authenticated_userid(request)
    if not user:
        raise Forbidden()
    db_user = u.show(user)
    result = {'user': user, 'db_user': db_user}
    return result

@view_config(route_name='userarea_recover_password', renderer='deform.jinja2')
def userarea_recover_password(context, request):
    """
    Display password recovery form
    """
    def recover_password_submit(context, request, deserialized, bind_params):
        """
        Submit password recovery form, email a token
        """
        email = deserialized.get("email")
        user = u.show_by_email(email)
        token = t.add_token(user, "password_recover")
        parsed = Template(s.show_setting("EMAIL"))
        route_name = "userarea_change_password_token"
        url = route_url(route_name, request, token=token)
        parsed = parsed.safe_substitute(what=s.show_setting("CHANGE_PASSWORD"),
                                        username=user.name, url=url,
                                        title=s.show_setting("TITLE"))
        mailer = get_mailer(request)
        message = Message(subject=s.show_setting("RECOVER_PASSWORD_SUBJECT"),
                          sender=s.show_setting("MAIL_SENDER"),
                          recipients=[user.email_address],
                          body=parsed)
        mailer.send(message)
        request.session.flash(s.show_setting("INFO_RECOVERY_EMAIL_SENT")
                              % email, INFO)
        return redirect(request, "home")
    result = rapid_deform(context, request, RecoverPasswordSchema,
                          recover_password_submit)
    if isinstance(result, dict):
        message = "Send Password Recovery Email"
        result.update({"title": message, "header": message})
    return result

def userarea_change_password_submit(context, request, deserialized, bind_params):
    """
    Submit change password form. 
    If a token was used, expire it then send changes to database.
    """
    user = authenticated_userid(request)
    token = bind_params.get("token")
    if token:
        user = token.user.name
        t.expire_token(token)
    password = deserialized.get("password")
    u.change_password(user, password)
    request.session.flash(s.show_setting("INFO_PASS_CHANGE"), INFO)
    return HTTPFound(location="/userarea/login", headers=forget(request))

@view_config(route_name='userarea_change_password_token',
             renderer='deform.jinja2')
def userarea_change_password_token(context, request):
    """
    Change password form (with a token)
    """
    t = TokenLib()
    token = None
    try:
        token = t.get_token(request.matchdict.get('token'),
                            False, "password_recover")
    except InvalidToken:
        request.session.flash(s.show_setting("ERROR_TOKEN"), ERROR)
        return redirect(request, "home")
    result = rapid_deform(context, request, ChangePasswordSchema,
                          userarea_change_password_submit, token=token)
    if isinstance(result, dict):
        message = "Change Password"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_change_password',
             permission='userarea_edit', renderer='deform.jinja2')
def userarea_change_password(context, request):
    """
    Change password form (without a token)
    """
    result = rapid_deform(context, request, ChangePasswordSchema,
                          userarea_change_password_submit)
    if isinstance(result, dict):
        message = "Change Password"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_edit', permission='userarea_edit',
             renderer='deform.jinja2')
def userarea_edit(context, request):
    """
    Edit the current user's profile
    """
    user = authenticated_userid(request)
    db_user = u.show(user)
    def edit_submit(context, request, deserialized, bind_params):
        """
        Submit profile data, save to database
        """
        db_user.full_name = deserialized.get("full_name")
        db_user.email_address = deserialized.get("email")
        db_user.sex = deserialized.get("sex")
        db_user.website = deserialized.get("website")
        db_user.aboutme = deserialized.get("about_me")
        db_user.timezone = deserialized.get("timezone")
        db_user.birthday = deserialized.get("birthday")
        transaction.commit()
        request.session.flash(s.show_setting("INFO_ACC_UPDATED"), INFO)
        return redirect(request, "userarea_profile", user=user)
    user = authenticated_userid(request)
    result = rapid_deform(context, request, EditUserSchema,
                          edit_submit, user=user, full_name=db_user.full_name,
                          email=db_user.email_address, sex=db_user.sex,
                          website=db_user.website, about_me=db_user.aboutme,
                          timezone=db_user.timezone, birthday=db_user.birthday)
    if isinstance(result, dict):
        message = "Editing Profile"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_register', renderer='deform.jinja2')
def userarea_register(context, request):
    """
    Display register form
    """
    def register_submit(context, request, deserialized, bind_params):
        """
        Submit register form, add user to database
        """
        email = deserialized.get("email")
        user = u.create_user(deserialized.get("username"),
                             deserialized.get("full_name"),
                             email, deserialized.get("password"))
        user.sex = deserialized.get("sex")
        user.website = deserialized.get("website")
        user.aboutme = deserialized.get("about_me")
        user.timezone = deserialized.get("timezone")
        user.birthday = deserialized.get("birthday")
        token = t.add_token(user, "register")
        parsed = Template(s.show_setting("EMAIL"))
        url = route_url("token_get", request, token=token)
        parsed = parsed.safe_substitute(what=s.show_setting("REGISTRATION"),
                                        username=user.name, url=url,
                                        title=s.show_setting("TITLE"))
        mailer = get_mailer(request)
        message = Message(subject=s.show_setting("REGISTRATION_SUBJECT"),
                          sender=s.show_setting("MAIL_SENDER"),
                          recipients=[user.email_address], body=parsed)
        mailer.send(message)
        user.groups.append(u.show_group("article"))
        request.session.flash(s.show_setting("INFO_ACTIVATON_EMAIL_SENT")
                              % email, INFO)
        return redirect(request, "home")
    result = rapid_deform(context, request, RegisterSchema, register_submit)
    if isinstance(result, dict):
        message = "Register"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_logout')
def userarea_logout(context, request):
    """
    Log the current user out
    """
    request.session['groupfinder'] = {}
    headers = forget(request)
    request.session.flash(s.show_setting("INFO_LOGOUT"), INFO)
    return redirect(request, "home", headers=headers)

@view_config(route_name='userarea_list', renderer='list.jinja2')
def userarea_list(context, request): #@ReservedAssignment
    """
    Display a list of users
    """
    message = "User List"
    route_name = "userarea_profile_two"
    return {'items': [(route_url(route_name, request, user=item[0]), item[1])
                      for item in u.list(False)],
            'title': message, 'header': message}

@view_config(route_name='userarea_admin_backup_settings', permission='backup')
def userarea_admin_backup_settings(context, request):
    m = MenuLib()
    res = request.response
    res.content_type = "application/json"
    res.text = str(json.dumps({"menus": m.to_dict(), "settings": s.to_dict()}))
    return res

@view_config(route_name='userarea_admin_restore_settings', permission='backup',
             renderer='deform.jinja2')
def userarea_admin_restore_settings(context, request):
    def restore_settings_submit(context, request, deserialized, bind_params):
        data = json.loads(deserialized['restore_settings_json_file']
                          ['fp'].read().decode())
        s.from_dict(data['settings'])
        MenuLib().from_dict(data['menus'])
        return redirect(request, "article_list")
    result = rapid_deform(context, request, RestoreSettingsSchema,
                          restore_settings_submit)
    if isinstance(result, dict):
        message = "Restore Settings from JSON File"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_edit_menu', permission='edit_menu',
             renderer='list.jinja2')
def userarea_admin_edit_menu(context, request):
    """
    Allow user to pick a menu group which is needed for editing items.
    See: userarea_admin_edit_menu_item
    """
    m = MenuLib()
    message = "Menu Groups"
    route_name = "userarea_admin_edit_menu_item"
    return {'items': [(route_url(route_name, request,
                                 group=item.name), item.name)
                      for item in m.list_groups()],
            'title': message, 'header': message}

@view_config(route_name='userarea_admin_edit_menu_item',
             permission='edit_menu', renderer='deform.jinja2')
def userarea_admin_edit_menu_item(context, request):
    """
    Display form that lets you edit menu items from a specified group.
    See: userarea_admin_edit_menu
    """
    m = MenuLib()
    def edit_menu_item_submit(context, request, deserialized, bind_params):
        """
        Save new list of menu items to database
        """
        group = bind_params["group"]
        new_menu = []
        for item in deserialized['menu']:
            for key in item.keys():
                if isinstance(item[key], str):
                    item[key] = item[key].replace("%20", " ")
            new_menu.append(item)
        group.menu_items = deserialize_relation(new_menu, Menu,
                                                {"group": group})
        request.session.flash(s.show_setting("INFO_MENU_UPDATED")
                              % group.name, INFO)
        return redirect(request, 'userarea_admin_edit_menu')
    group = m.show_group(request.matchdict.get('group'))
    result = rapid_deform(context, request, EditMenuItems,
                          edit_menu_item_submit, group=group,
                          menu=serialize_relation(group.menu_items))
    if isinstance(result, dict):
        message = "Editing " + group.name
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_edit_menu_group',
             permission='edit_menu', renderer='deform.jinja2')
def userarea_admin_edit_menu_group(context, request):
    """
    Display form that lets you edit menu groups
    """
    m = MenuLib()
    def edit_menu_group_submit(context, request, deserialized, bind_params):
        """
        Save new list of menu groups to database
        """
        groups = set([g.name for g in bind_params["groups"]])
        deserialized_groups = set(deserialized['menu_groups'])
        list(map(m.add_group, deserialized_groups - groups))
        list(map(m.delete_group, groups - deserialized_groups))
        request.session.flash(s.show_setting("INFO_MENU_GROUP_UPDATED"), INFO)
        return redirect(request, 'userarea_admin_edit_menu')
    groups = m.list_groups().all()
    menu_groups = [x['name'] for x in serialize_relation(groups)]
    result = rapid_deform(context, request, MenuGroup,
                          edit_menu_group_submit, groups=groups,
                          menu_groups=menu_groups)
    if isinstance(result, dict):
        message = "Editing Menu Groups"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_edit_acl',
             permission='edit_acl', renderer='deform.jinja2')
def userarea_admin_edit_acl(context, request):
    """
    Display a form that lets you edit the access control list
    """
    def edit_acl_submit(context, request, deserialized, bind_params):
        """
        Save new access control list to database
        """
        context.__acl__ = JsonList(map(dict_to_acl, deserialized['acl']))
        request.session['groupfinder'] = {}
        request.session.flash(s.show_setting("INFO_ACL_UPDATED"), INFO)
        return redirect(request, 'home')
    result = rapid_deform(context, request, EditACL, edit_acl_submit, 
                          acl=map(acl_to_dict, context.__acl__))
    if isinstance(result, dict):
        message = "Editing Access Control List"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_list_settings',
             permission='edit_settings', renderer='list.jinja2')
def userarea_admin_list_settings(context, request):
    """
    Allow user to pick a setting which is needed for editing it.
    See: userarea_admin_edit_settings
    """
    message = "Settings"
    route_name = "userarea_admin_edit_settings"
    return {'items': [(route_url(route_name, request,
                                 name=item.name), item.name)
                      for item in s.list()],
            'title': message, 'header': message}

@view_config(route_name='userarea_admin_edit_settings',
             permission='edit_settings', renderer='deform.jinja2')
def userarea_admin_edit_settings(context, request):
    """
    Display a form that lets you edit the settings table
    """
    def edit_setting_submit(context, request, deserialized, bind_params):
        """
        Save new setting to database
        """
        s.update(bind_params['name'], deserialized['value'])
        return redirect(request, 'userarea_admin_list_settings')
    name = request.matchdict.get('name')
    result = rapid_deform(context, request, SettingSchema, edit_setting_submit, 
                          name=name, value=s.show_setting(name).value)
    if isinstance(result, dict):
        message = "Editing Settings"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_edit_template',
             permission='edit_settings', renderer='deform.jinja2')
def userarea_admin_edit_template(context, request):
    """
    Display a form that lets you edit the main template
    """
    setting_data = request.registry.settings.get("main_template")
    main_path = resolve(setting_data).abspath()
    def edit_template_submit(context, request, deserialized, bind_params):
        """
        Save new template
        """
        open(main_path, "w", newline="\n").write(deserialized['value'])
        return redirect(request, 'home')
    result = rapid_deform(context, request, SettingSchema,
                          edit_template_submit, value=open(main_path).read())
    if isinstance(result, dict):
        message = "Editing Template"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_file_upload',
             permission='file_upload', renderer='userarea/file_upload.jinja2')
def userarea_admin_file_upload(context, request):
    message = "File Upload"
    result = []
    setting_data = request.registry.settings.get("static_path")
    static_path = resolve(setting_data).abspath()
    if 'path' in request.GET:
        new_static_path = os.path.join(static_path, request.GET['path'])
    else:
        new_static_path = static_path
    if 'datafile' in request.POST:
        data_file = request.POST['datafile']
        shutil.copyfileobj(data_file.file,
                           open(os.path.join(new_static_path,
                                             data_file.filename), "wb"))
    for item in os.listdir(new_static_path):
        if os.path.isdir(os.path.join(new_static_path, item)):
            if 'path' in request.GET:
                result.append((True, "?path=%s/%s" % 
                               (request.GET['path'], item), item))
            else:
                result.append((True, "?path=" + item, item))
        else:
            if 'path' in request.GET:
                result.append((False, "/static/%s/%s" % 
                               (request.GET['path'], item), item))
            else:
                result.append((False, "/static/" + item, item))
    return {'items': result, 'title': message, 'header': message}

@view_config(route_name='userarea_admin_manage_users',
             permission='group:admin', renderer='userarea/manage_users.jinja2')
def userarea_admin_manage_users(context, request):
    """
    Show table of users
    """
    return {"users": u.list(as_obj=True)}

@view_config(route_name='userarea_admin_manage_user',
             permission='group:admin', renderer='deform.jinja2')
def userarea_admin_manage_user(context, request):
    """
    Manage a user
    """
    user = request.matchdict.get("name")
    db_user = u.show(user)
    def manage_user_submit(context, request, deserialized, bind_params):
        """
        Save user
        """
        db_user.full_name = deserialized.get("full_name")
        db_user.email_address = deserialized.get("email")
        db_user.sex = deserialized.get("sex")
        db_user.website = deserialized.get("website")
        db_user.aboutme = deserialized.get("about_me")
        db_user.timezone = deserialized.get("timezone")
        db_user.birthday = deserialized.get("birthday")
        db_user.banned = deserialized.get("banned")
        db_user.groups = []
        for item in deserialized.get("groups"):
            db_user.groups.append(u.show_group(item))
        if deserialized.get("password"):
            db_user.password = deserialized.get("password")
        transaction.commit()
        request.session.flash(s.show_setting("INFO_ACC_UPDATED"), INFO)
        return redirect(request, 'userarea_admin_manage_users')
    result = rapid_deform(context, request, EditAdminUserSchema, 
                          manage_user_submit, full_name=db_user.full_name,
                          email=db_user.email_address, website=db_user.website,
                          birthday=db_user.birthday, about_me=db_user.aboutme,
                          sex=db_user.sex, timezone=db_user.timezone,
                          banned=db_user.banned, 
                          groups=[x.name for x in db_user.groups])
    if isinstance(result, dict):
        message = "Managing user " + user
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_delete_user', permission='group:admin')
def userarea_admin_delete_user(context, request):
    """
    Delete a user
    """
    user = request.matchdict.get("name")
    u.delete_user(user)
    return redirect(request, 'userarea_admin_manage_users')