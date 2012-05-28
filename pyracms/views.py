from .__init__ import main_path, static_path
from .deform_schemas.article import EditArticleSchema
from .deform_schemas.userarea import (LoginSchema, RegisterSchema, 
    ChangePasswordSchema, RecoverPasswordSchema, EditUserSchema)
from .deform_schemas.userarea_admin import (EditACL, MenuGroup, EditMenuItems, 
    SettingSchema)
from .errwarninfo import (INFO_DELETED, INFO, ERROR, ERROR_NOT_FOUND, INFO_REVERT, 
    ERROR_INVALID_USER_PASS, INFO_LOGIN, INFO_LOGOUT, INFO_ACTIVATON_EMAIL_SENT, 
    ERROR_TOKEN, INFO_PASS_CHANGE, INFO_RECOVERY_EMAIL_SENT, INFO_ACC_UPDATED, 
    INFO_ACL_UPDATED, INFO_MENU_GROUP_UPDATED, INFO_MENU_UPDATED)
from .lib.articlelib import ArticleLib, PageNotFound
from .lib.helperlib import (acl_to_dict, dict_to_acl, serialize_relation, 
    deserialize_relation, get_username, redirect, rapid_deform)
from .lib.menulib import MenuLib
from .lib.settingslib import SettingsLib
from .lib.tokenlib import TokenLib, InvalidToken
from .lib.userlib import UserLib
from .models import Menu
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.security import remember, forget, authenticated_userid
from pyramid.url import route_url
from pyramid.view import view_config
import os
import shutil


u = UserLib()
t = TokenLib()

@view_config(route_name='userarea_login',
             renderer='userarea/login.jinja2')
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
            request.session.flash(INFO_LOGIN, INFO)
            return redirect(request, "home", headers=headers)
        else:
            request.session.flash(ERROR_INVALID_USER_PASS, ERROR)
            return redirect(request, "userarea_login")
    return rapid_deform(context, request, LoginSchema, login_submit)

@view_config(route_name='userarea_profile',
             renderer='userarea/profile.jinja2')
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
        print(t.add_token(u.show_by_email(email), "password_recover"))
        request.session.flash(INFO_RECOVERY_EMAIL_SENT % email, INFO)
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
    request.session.flash(INFO_PASS_CHANGE, INFO)
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
        request.session.flash(ERROR_TOKEN, ERROR)
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
    def edit_submit(context, request, deserialized, bind_params):
        """
        Submit profile data, save to database
        """
        user = authenticated_userid(request)
        u.update_user(user, deserialized.get("display_name"),
                      deserialized.get("email"))
        request.session.flash(INFO_ACC_UPDATED, INFO)
        return redirect(request, "userarea_profile", user=user)
    user = authenticated_userid(request)
    result = rapid_deform(context, request, EditUserSchema,
                          edit_submit, user=user)
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
                             deserialized.get("display_name"),
                             email,
                             deserialized.get("password"))
        user.groups.append(u.show_group("article"))
        print(t.add_token(user, "register"))
        request.session.flash(INFO_ACTIVATON_EMAIL_SENT % email, INFO)
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
    request.session.flash(INFO_LOGOUT, INFO)
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
        context.__acl__ = set(map(dict_to_acl, deserialized['acl']))
        request.session['groupfinder'] = {}
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

@view_config(route_name='userarea_admin_list_settings',
             permission='edit_settings', renderer='list.jinja2')
def userarea_admin_list_settings(context, request):
    """
    Allow user to pick a setting which is needed for editing it.
    See: userarea_admin_edit_settings
    """
    s = SettingsLib()
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
    s = SettingsLib()
    def edit_setting_submit(context, request, deserialized, bind_params):
        """
        Save new setting to database
        """
        s.update(bind_params['name'], deserialized['value'])
        return redirect(request, 'userarea_admin_list_settings')
    name = request.matchdict.get('name')
    appstruct = {'value': s.show_setting(name).value}
    result = rapid_deform(context, request, SettingSchema,
                          edit_setting_submit, appstruct=appstruct,
                          name=name)
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
    def edit_template_submit(context, request, deserialized, bind_params):
        """
        Save new template
        """
        open(main_path, "w", newline="\n").write(deserialized['value'])
        return redirect(request, 'home')
    appstruct = {'value': open(main_path).read()}
    result = rapid_deform(context, request, SettingSchema,
                          edit_template_submit, appstruct=appstruct)
    if isinstance(result, dict):
        message = "Editing Template"
        result.update({"title": message, "header": message})
    return result

@view_config(route_name='userarea_admin_file_upload',
             permission='file_upload', renderer='file_upload.jinja2')
def userarea_admin_file_upload(context, request):
    message = "File Upload"
    result = []
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
                result.append(("?path=%s/%s" % (request.GET['path'], item),
                               item))
            else:
                result.append(("?path=" + item, item))
        else:
            if 'path' in request.GET:
                result.append(("/static/%s/%s" % (request.GET['path'], item),
                               item))
            else:
                result.append(("/static/" + item, item))
    return {'items': result, 'title': message, 'header': message}

@view_config(route_name='css')
def css(request):
    s = SettingsLib()
    css_data = s.show_setting("CSS").value
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

@view_config(route_name='home', renderer='article/article.jinja2',
             permission='article_view')
@view_config(route_name='article_read', renderer='article/article.jinja2',
             permission='article_view')
@view_config(route_name='article_read_revision',
             renderer='article/article.jinja2', permission='article_view')
def article_read(context, request):
    """
    Display an article
    """
    c = ArticleLib()
    result = {}
    page_id = request.matchdict.get('page_id') or "Front_Page"
    revision_id = request.matchdict.get('revision')
    try:
        page = c.show_page(page_id)
        revision = c.show_revision(page, revision_id)
        if page.deleted:
            return HTTPFound(location=route_url("article_update",
                                                request, page_id=page.name))
        else:
            result.update({'page': page, 'revision': revision})
            return result
    except PageNotFound:
        return redirect(request, "article_create", page_id=page_id)

@view_config(route_name='article_delete', permission='article_delete')
def article_delete(context, request):
    """
    Delete an article
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        c.delete(request, c.show_page(page_id), u.show(get_username(request)))
        request.session.flash(INFO_DELETED % page_id, INFO)
        return redirect(request, "article_list")
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % page_id, ERROR)
        return redirect(request, "article_list")

@view_config(route_name='article_list', permission='article_list',
             renderer='article/article_list.jinja2')
def article_list(context, request):
    """
    Show a list of articles
    """
    c = ArticleLib()
    return {'pages': c.list()}

@view_config(route_name='article_list_revisions',
             permission='article_list_revisions',
             renderer='article/article_list_revisions.jinja2')
def article_list_revisions(context, request):
    """
    Show a list of article revisions, every time a change is made, 
    a revision is added
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        page = c.show_page(page_id)
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % page_id, ERROR)
        return redirect(request, "article_list")
    return {'page': page}

@view_config(route_name='article_update', permission='article_update',
             renderer='article/article_update.jinja2')
def article_update(context, request):
    """
    Display edit article form
    """
    c = ArticleLib()
    def article_update_submit(context, request, deserialized, bind_params):
        """
        Add a article revision to the database
        """
        page = bind_params.get("page")
        name = request.matchdict.get("page_id")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        c.update(request, page, article, summary,
                 u.show(get_username(request)), tags)
        page.display_name = deserialized.get("display_name")
        return redirect(request, "article_read", page_id=name)
    matchdict_get = request.matchdict.get
    page = c.show_page(matchdict_get('page_id'))
    revision = c.show_revision(page, matchdict_get('revision'))
    return rapid_deform(context, request, EditArticleSchema,
                        article_update_submit, page=page,
                        revision=revision, cache=False)

@view_config(route_name='article_create', permission='article_create',
             renderer='article/article_update.jinja2')
def article_create(context, request):
    """
    Display create a new article form
    """
    c = ArticleLib()
    def article_create_submit(context, request, deserialized, bind_params):
        """
        Save new article to the database
        """
        name = request.matchdict.get("page_id")
        display_name = deserialized.get("display_name")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        c.create(request, name, display_name, article, summary,
                 u.show(get_username(request)), tags)
        return redirect(request, "article_read", page_id=name)
    return rapid_deform(context, request, EditArticleSchema,
                        article_create_submit,
                        page_id=request.matchdict.get("page_id"))

@view_config(route_name='article_revert', permission='article_revert')
def article_revert(context, request):
    """
    Revert an old revision, basically makes a new revision with old contents
    """
    c = ArticleLib()
    matchdict_get = request.matchdict.get
    try:
        page = c.show_page(matchdict_get('page_id'))
        c.revert(request, page,
                 c.show_revision(page, matchdict_get('revision')),
                 u.show(get_username(request)))
        request.session.flash(INFO_REVERT % page.name, INFO)
        return redirect(request, "article_read", page_id=page.name)
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % matchdict_get('page_id'),
                              ERROR)
        return redirect(request, "article_list")

@view_config(route_name='article_switch_renderer', permission='switch_renderer')
def article_switch_renderer(context, request):
    """
    Use another rendering engine for the page
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    c.switch_renderer(page_id)
    return redirect(request, "article_read", page_id=page_id)
