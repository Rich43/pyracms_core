from .models import DBSession
from .security import groupfinder
from .lib.widgetlib import WidgetLib
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from sqlalchemy import engine_from_config

def add_renderer_globals(event):
    event['w'] = WidgetLib()

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    authentication_policy = AuthTktAuthenticationPolicy('seekrit', 
                                                        callback=groupfinder)
    authorization_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
                          root_factory='.models.RootFactory',
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path("pyracms:templates")
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view("dstatic", "deform:static", cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('css', '/css')
    config.add_route('login', '/login')
    config.add_route('invalid_login', '/invalid_login')
    config.add_route('logout', '/logout')
    config.scan()
    return config.make_wsgi_app()

