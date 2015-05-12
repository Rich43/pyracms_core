from .lib.settingslib import SettingsLib
from .lib.widgetlib import WidgetLib
from .models import DBSession
from .security import groupfinder
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from sqlalchemy import engine_from_config
from .views import dummy_home

def add_renderer_globals(event):
    event['w'] = WidgetLib()
    event['s'] = SettingsLib()

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
                          root_factory='.factory.RootFactory',
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy,
                          session_factory=session_factory)
    if hasattr(config, "add_jinja2_search_path"):
        config.add_jinja2_search_path(
                        settings.get('jinja2_search_path'))
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_static_view('static', settings.get('static_path'), 
                           cache_max_age=3600)
    config.add_static_view('static-deform', 'deform:static')
    if settings.get("enable_pyracms_home"):
        config.add_view(dummy_home, route_name="home", 
                        renderer="dummy_home.jinja2")
        config.add_route('home', '/')
    config.add_route('css', '/css')
    config.add_route('redirect_one', '/redirect/{route_name}')
    config.add_route('redirect_two', '/redirect/{route_name}/{type}')
    
    # Tokens and Search
    config.add_route('token_get', '/token/{token}')
    config.add_route('search', '/search/{query}')
    
    # Userarea routes
    config.add_route('userarea_login', '/userarea/login')
    config.add_view(view=".views.userarea_login",
                    context="pyramid.httpexceptions.HTTPForbidden",
                    renderer="login.jinja2")
    config.add_route('userarea_logout', '/userarea/logout')
    config.add_route('userarea_profile', '/userarea/profile')
    config.add_route('userarea_profile_two', '/userarea/profile/{user}')
    config.add_route('userarea_edit', '/userarea/edit')
    config.add_route('userarea_recover_password',
                     '/userarea/recover_password')
    config.add_route('userarea_change_password', '/userarea/change_password')
    config.add_route('userarea_change_password_token',
                     '/userarea/change_password/{token}')
    config.add_route('userarea_register', '/userarea/register')
    config.add_route('userarea_list', '/userarea/list')

    # Userarea Admin routes
    config.add_route('userarea_admin_edit_menu', '/userarea_admin/edit_menu')
    config.add_route('userarea_admin_edit_menu_item',
                     '/userarea_admin/edit_menu/{group}')
    config.add_route('userarea_admin_edit_menu_group',
                     '/userarea_admin/edit_menu_group')
    config.add_route('userarea_admin_edit_acl', '/userarea_admin/edit_acl')
    config.add_route('userarea_admin_list_settings',
                     '/userarea_admin/list_settings')
    config.add_route('userarea_admin_edit_settings',
                     '/userarea_admin/edit_setting/{name}')
    config.add_route('userarea_admin_edit_template',
                     '/userarea_admin/edit_template')
    config.add_route('userarea_admin_file_upload',
                     '/userarea_admin/file_upload')
    config.add_route('userarea_admin_backup_settings',
                     '/userarea_admin/backup_settings')
    config.add_route('userarea_admin_restore_settings',
                     '/userarea_admin/restore_settings')
    config.add_route('userarea_admin_manage_users',
                     '/userarea_admin/manage_users')
    config.add_route('userarea_admin_manage_user',
                     '/userarea_admin/manage_users/{name}')
    config.add_route('userarea_admin_delete_user',
                     '/userarea_admin/delete_user/{name}')
    config.scan()
    return config.make_wsgi_app()

