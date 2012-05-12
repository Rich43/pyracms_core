from .lib.helperlib import redirect
from .lib.userlib import UserLib
from pyramid.security import remember, forget
from pyramid.view import view_config

u = UserLib()

@view_config(route_name='home', renderer='index.jinja2')
def home(request):
    return {}

@view_config(route_name='login')
def login(request):
    if 'Username' in request.POST and 'Password' in request.POST:
        if u.login(request.POST['Username'], request.POST['Password']):
            headers = remember(request, request.POST['Username'])
            return redirect(request, 'home', headers=headers)
        else:
            return redirect(request, 'invalid_login')
    else:
        return redirect(request, 'home')
    
@view_config(route_name='invalid_login', renderer='auth/invalid_login.jinja2')
def invalid_login(request):
    return {}

@view_config(route_name='logout')
def logout(request):
    return redirect(request, 'home', headers=forget(request))

