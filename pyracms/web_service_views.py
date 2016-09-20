""" Cornice services.
"""
import json

from colander import MappingSchema, SchemaNode, String
from cornice.ext.spore import generate_spore_description
from cornice.service import Service, get_services
from pyracms.lib.userlib import UserLib
from webob import Response, exc

u = UserLib()


class _401(exc.HTTPError):
    def __init__(self, msg='Unauthorized'):
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def valid_token(request):
    header = 'X-Messaging-Token'
    htoken = request.headers.get(header)
    if htoken is None:
        raise _401()
    try:
        user, token = htoken.split(',', 1)
    except ValueError:
        raise _401()

    valid = u.exists(user)
    if valid:
        valid = u.show(user).api_uuid == token
    if not valid:
        raise _401()

    request.validated['user'] = user


class LoginSchema(MappingSchema):
    username = SchemaNode(String(), location="body", type='str')
    password = SchemaNode(String(), location="body", type='str')


spore = Service('spore', path='/spore', renderer='json')


@spore.get()
def api_get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Pyracms Service',
                                      request.application_url, '1.0')


auth = Service(name='auth', path='/api/userarea/auth',
               description="User login and list")


@auth.get()
def api_get_users(request):
    """Returns a list of all users."""
    users = {}
    for user in u.list(as_obj=True):
        users[user.name] = user.display_name
    return users


@auth.get()
def api_user_list(request):
    """Lists users."""
    users = {}
    for user in u.list(as_obj=True):
        users[user.name] = user.full_name
    return users


@auth.post(schema=LoginSchema)
def api_user_login(request):
    username = request.json_body['username']
    if u.login(username, request.json_body['password']):
        user = u.show(username)
        return {"login_success": user.api_uuid}
    else:
        request.errors.add('userarea', 'login_fail',
                           'Invalid username/password')
