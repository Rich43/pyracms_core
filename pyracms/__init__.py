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
from os.path import dirname, join

main_path = join(dirname(__file__), "templates", "main.jinja2")
static_path = join(dirname(__file__), "static")

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
    config.add_route('redirect_one', '/redirect/{route_name}')
    config.add_route('redirect_two', '/redirect/{route_name}/{type}')

    # Userarea routes
    config.add_route('userarea_login', '/userarea/login')
    config.add_view(view=".views.userarea_login",
                    context="pyramid.httpexceptions.HTTPForbidden",
                    renderer="userarea/login.jinja2")
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
    config.add_route('article_switch_renderer',
                     '/article/switch_renderer/{page_id}')
    config.scan()
    return config.make_wsgi_app()

