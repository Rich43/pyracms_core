from .lib.helperlib import redirect
from .lib.userlib import UserLib
from pyramid.security import remember, forget
from pyramid.view import view_config

u = UserLib()

@view_config(route_name='home', renderer='index.jinja2')
def home(request):
    return {'css_links':['/css']}

@view_config(route_name='login')
def login(request):
    if 'username' in request.POST and 'password' in request.POST:
        if u.login(request.POST['username'], request.POST['password']):
            headers = remember(request, request.POST['username'])
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

@view_config(route_name='css')
def css(request):
    res = request.response
    res.article_type = "text/css"
    res.text = ""
    return res

