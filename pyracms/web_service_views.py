""" Cornice services.
"""
import json
import magic
import webob
import ntpath
from colander import MappingSchema, SchemaNode, String
from cornice.service import Service
from cornice.validators import colander_body_validator
from webob import Response, exc

from .lib.filelib import FileLib, APIFileNotFound
from .lib.userlib import UserLib, UserNotFound
from .lib.menulib import MenuLib, MenuGroupNotFound

APP_JSON = "application/json"

u = UserLib()
m = MenuLib()


class _401(exc.HTTPError):
    def __init__(self, msg='Unauthorized'):
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def get_token(request):
    header = 'X-Messaging-Token'
    htoken = request.headers.get(header)
    if htoken is None:
        raise _401("X-Messaging-Token missing")
    try:
        user = u.show_by_token(htoken.strip())
    except UserNotFound:
        raise _401("Token '%s' Not Found" % htoken)
    return user, htoken


def valid_token(request, **kwargs):
    user, token = get_token(request)
    request.validated['user'] = user.name
    request.validated['user_db'] = user


def valid_permission(request, permission):
    user = request.validated['user']
    if permission in u.list_users_permissions(user):
        return True
    else:
        return False


def valid_group(request, group):
    user = request.validated['user']
    if group in u.list_users_groups(user):
        return True
    else:
        return False


def valid_qs_int(request, what):
    try:
        if request.params.get(what):
            int(request.params.get(what))
        else:
            request.errors.add('querystring', 'missing',
                               '%s missing from query string.' % what)
            return False
    except ValueError:
        request.errors.add('querystring', 'type',
                           '%s in query string must be a Integer.' % what)
        return False
    return True


def valid_qs(request, what):
    if not request.params.get(what):
        request.errors.add('querystring', 'missing',
                           '%s missing from query string.' % what)
        return False
    return True


def valid_file_key(request, **kwawgs):
    try:
        file_key = request.json_body.get("file_key")
    except (json.decoder.JSONDecodeError, UnicodeDecodeError):
        request.errors.add('body', 'missing',
                           'file_key missing from body.')
        return
    if not file_key:
        request.errors.add('body', 'missing',
                           'file_key missing from body.')
        return
    f = FileLib(request)
    try:
        f.api_show(file_key)
    except APIFileNotFound:
        request.errors.add('body', 'not_found',
                           'file_key not found in database.')


class LoginSchema(MappingSchema):
    username = SchemaNode(String(), location="body", type='str')
    password = SchemaNode(String(), location="body", type='str')


auth = Service(name='auth', path='/api/userarea/auth',
               description="User login and list")


@auth.get()
def api_user_list(request):
    """Lists users."""
    users = {}
    for user in u.list(as_obj=True):
        users[user.name] = user.full_name
    return users


@auth.post(schema=LoginSchema, validators=colander_body_validator,
           content_type=APP_JSON)
def api_user_login(request):
    username = request.json_body['username']
    if u.login(username, request.json_body['password']):
        user = u.show(username)
        return {"login_success": user.api_uuid}
    else:
        request.errors.add('body', 'login_fail',
                           'Invalid username/password')


file_upload = Service(name='file_upload', path='/api/file_upload',
                      description="Upload files, returns a uuid/key")


def api_valid_get_qs(request, **kwargs):
    valid_qs(request, "uuid")


@file_upload.get(validators=api_valid_get_qs)
def api_file_upload_get(request):
    """Check API uuid/key."""
    f = FileLib(request)
    f.api_delete_expired()
    try:
        file_obj = f.api_show(request.params['uuid'])
        return {"uuid": file_obj.name, "created": str(file_obj.created),
                "expires": str(file_obj.expires),
                "size": file_obj.file_obj.size,
                "mimetype": file_obj.file_obj.mimetype,
                "is_picture": file_obj.file_obj.is_picture,
                "is_video": file_obj.file_obj.is_video,
                "filename": file_obj.file_obj.name}
    except APIFileNotFound:
        request.errors.add('body', 'not_found', 'UUID Not Found')


def api_file_upload_validator(request, **kwawgs):
    if "data" not in request.POST:
        request.errors.add('body', 'missing',
                           'data field not found in POST.')
        return
    if not isinstance(request.POST['data'], webob.compat.cgi_FieldStorage):
        request.errors.add('body', 'invalid',
                           'data is invalid data type.')


@file_upload.post(validators=api_file_upload_validator)
def api_file_upload_post(request):
    f = FileLib(request)
    magic_obj = magic.Magic(mime=True)
    post_data = request.POST['data']
    post_file = post_data.file
    mimetype = magic_obj.from_buffer(post_file.read(1024))
    post_file.seek(0)
    file_upload_obj = f.api_write(ntpath.basename(post_data.filename),
                                  post_file, mimetype)
    return {"status": "ok", "mimetype": mimetype, "uuid": file_upload_obj.name,
            "created": str(file_upload_obj.created),
            "expires": str(file_upload_obj.expires),
            "size": file_upload_obj.file_obj.size,
            "is_picture": file_upload_obj.file_obj.is_picture,
            "is_video": file_upload_obj.file_obj.is_video,
            "filename": file_upload_obj.file_obj.name}

guest_token = Service(name='guest_token', path='/api/guest_token',
                      description="Get guest token")
@guest_token.get()
def get_guest_token(request):
    try:
        user = u.show("system.Everyone")
    except UserNotFound:
        request.errors.add('body', 'not_found',
                           'guest not found in database.')
    return user.api_uuid

menu_group_list = Service(name='menu_group_list', path='/api/menu_group/list',
                          description="List menu groups")


@menu_group_list.get()
def list_menu_group(request):
    result = [{"name": group.name, "id": group.id} for group in m.list_groups()]
    return result


menu_list = Service(name='menu_group_item', path='/api/menu/list',
                     description="Generate a list of menu items")


def api_valid_menu_group(request, **kwargs):
    if valid_qs(request, "group"):
        try:
            m.show_group(request.params['group'])
        except MenuGroupNotFound:
            request.errors.add('querystring', 'not_found',
                               'group not found in database.')

@menu_list.get(validators=(valid_token, api_valid_menu_group))
def get_menu_group(request):
    grp_name = request.params['group']
    grp_obj = m.show_group(grp_name)
    result = {}
    for item in grp_obj.menu_items:
        if not valid_permission(request, item.permissions):
            continue
        url = ""
        update = {}
        if item.type == "route":
            update = {"route_name": item.route_name,
                      "route_json": json.loads(item.route_json)}
        else:
            url = item.url
        result[item.position] = {"name": item.name, "web_url": url,
                                 "permissions": item.permissions,
                                 "type": item.type, "id": item.id}
        result[item.position].update(update)
    return result