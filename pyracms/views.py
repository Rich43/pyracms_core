from .deform_schemas.article import EditArticleSchema
from .deform_schemas.userarea import (LoginSchema, RegisterSchema, 
    ChangePasswordSchema, RecoverPasswordSchema, EditUserSchema)
from .deform_schemas.userarea_admin import (EditACL, MenuGroup, EditMenuItems, 
    SettingSchema, RestoreBackupSchema)
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
from pyramid.security import (remember, forget, authenticated_userid, 
                              has_permission)
from pyramid.url import route_url
from pyramid.view import view_config
from pyramid.path import AssetResolver
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from string import Template
import os
import shutil

u = UserLib()
t = TokenLib()
s = SettingsLib()
resolve = AssetResolver().resolve
ERROR = 'error'
WARN = 'warn'
INFO = 'info'

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
                        appstruct={"redirect_url":redirect_url})

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
    def edit_submit(context, request, deserialized, bind_params):
        """
        Submit profile data, save to database
        """
        user = authenticated_userid(request)
        u.update_user(user, deserialized.get("display_name"),
                      deserialized.get("email"))
        request.session.flash(s.show_setting("INFO_ACC_UPDATED"), INFO)
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
        token = t.add_token(user, "register")
        parsed = Template(s.show_setting("EMAIL"))
        url = route_url("token_get", request, token=token)
        parsed = parsed.safe_substitute(what=s.show_setting("REGISTRATION"),
                                        username=user.name, url=url,
                                        title=s.show_setting("TITLE"))
        mailer = get_mailer(request)
        message = Message(subject=s.show_setting("REGISTRATION_SUBJECT"),
                          sender=s.show_setting("MAIL_SENDER"),
                          recipients=[user.email_address],
                          body=parsed)
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

@view_config(route_name='userarea_admin_backup_articles', permission='backup')
def userarea_admin_backup_articles(context, request):
    a = ArticleLib()
    res = request.response
    res.content_type = "application/json"
    res.text = str(a.to_json())
    return res

@view_config(route_name='userarea_admin_restore_articles', permission='backup',
             renderer='deform.jinja2')
def userarea_admin_restore_articles(context, request):
    def restore_backup_submit(context, request, deserialized, bind_params):
        a = ArticleLib()
        a.from_json(request, deserialized['restore_backup_json_file']
                    ['fp'].read().decode())
        return redirect(request, "article_list")
    result = rapid_deform(context, request, RestoreBackupSchema,
                          restore_backup_submit)
    if isinstance(result, dict):
        message = "Restore Articles from JSON File"
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
        request.session.flash(s.show_setting("INFO_MENU_GROUP_UPDATED"), INFO)
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
        request.session.flash(s.show_setting("INFO_ACL_UPDATED"), INFO)
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
    setting_data = request.registry.settings.get("main_template")
    main_path = resolve(setting_data).abspath()
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

@view_config(route_name='css')
def css(request):
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
        elif page.private and not has_permission("set_private", context, 
                                                 request):
            raise Forbidden()
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
        request.session.flash(s.show_setting("INFO_DELETED")
                              % page_id, INFO)
        return redirect(request, "article_list")
    except PageNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
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
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
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
        request.session.flash(s.show_setting("INFO_REVERT")
                              % page.name, INFO)
        return redirect(request, "article_read", page_id=page.name)
    except PageNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % matchdict_get('page_id'), ERROR)
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

@view_config(route_name='article_set_private', permission='set_private')
def article_set_private(context, request):
    """
    Make page private
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    c.set_private(page_id)
    return redirect(request, "article_read", page_id=page_id)
