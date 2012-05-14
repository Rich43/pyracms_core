from .models import DBSession
from .security import groupfinder
from .lib.widgetlib import WidgetLib
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from sqlalchemy import engine_from_config
from pyramid.session import UnencryptedCookieSessionFactoryConfig

def add_renderer_globals(event):
    event['w'] = WidgetLib()

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # Get database settings
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    
    # Setup auth + auth policy's
    authentication_policy = AuthTktAuthenticationPolicy(
                            settings.get('auth_secret'), callback=groupfinder)
    authorization_policy = ACLAuthorizationPolicy()
    
    # Configure session support
    session_factory = UnencryptedCookieSessionFactoryConfig(
                                            settings.get('session_secret'))
    
    # Add basic configuration
    config = Configurator(settings=settings,
                          root_factory='.models.RootFactory',
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy,
                          session_factory=session_factory)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path("pyracms:templates")
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view("dstatic", "deform:static", cache_max_age=3600)
    config.add_route('css', '/css')
    
    # Userarea routes
    config.add_route('userarea_login', '/userarea/login')
    config.add_route('userarea_logout', '/userarea/logout')
    
    # Article Routes
    config.add_route('home', '/')
    config.add_route('article_read', '/article/item/{page_id}')
    config.add_route('article_read_revision', 
                     '/article/item/{page_id}/{revision}')
    config.add_route('article_list', '/article/list')
    config.add_route('article_revert', 
                     '/article/revert/{page_id}/{revision}')
    config.add_route('article_delete', '/article/delete/{page_id}')
    config.add_route('article_create', '/article/create/{page_id}')
    config.add_route('article_update', '/article/update/{page_id}')
    config.add_route('article_list_revisions', 
                     '/article/list_revisions/{page_id}')
    
    config.scan()
    return config.make_wsgi_app()

