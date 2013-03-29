from ..lib.userlib import UserLib
from ..models import DBSession, Base, Menu, MenuGroup, Settings, RootFactory
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone, Allow, Authenticated
from sqlalchemy import engine_from_config
import os
import sys
import transaction
from pyracms.models import ArticleRenderers

def usage(argv):
    cmd = os.path.basename(argv[0])
    print(('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        # Default Users
        u = UserLib()
        admin_user = u.create_user("admin", "Admin User", "admin@admin.com",
                                   "admin")
        u.create_user(Everyone, "Guest User", "guest@guest.com", "guest")

        # Default Groups
        u.create_group("article", "Ability to Add, Edit, Delete, " +
                       "Revert and Protect Articles.", [admin_user])
        u.create_group("admin", "All Access!", [admin_user])

        # Default ACL
        acl = RootFactory()
        acl.__acl__.add((Allow, Everyone, Everyone))
        acl.__acl__.add((Allow, Authenticated, Authenticated))
        acl.__acl__.add((Allow, Authenticated, "not_authenticated"))
        acl.__acl__.add((Allow, Authenticated, "userarea_edit"))
        acl.__acl__.add((Allow, Everyone, "article_view"))
        acl.__acl__.add((Allow, Everyone, "article_list"))
        acl.__acl__.add((Allow, Everyone, "article_list_revisions"))
        acl.__acl__.add((Allow, "group:admin", "group:admin"))
        acl.__acl__.add((Allow, "group:admin", "edit_menu"))
        acl.__acl__.add((Allow, "group:admin", "edit_acl"))
        acl.__acl__.add((Allow, "group:admin", "edit_settings"))
        acl.__acl__.add((Allow, "group:admin", "switch_renderer"))
        acl.__acl__.add((Allow, "group:admin", "file_upload"))
        acl.__acl__.add((Allow, "group:admin", "backup"))
        acl.__acl__.add((Allow, "group:admin", "set_private"))
        acl.__acl__.add((Allow, "group:article", "group:article"))
        acl.__acl__.add((Allow, "group:article", "article_view"))
        acl.__acl__.add((Allow, "group:article", "article_list"))
        acl.__acl__.add((Allow, "group:article", "article_list_revisions"))
        acl.__acl__.add((Allow, "group:article", "article_create"))
        acl.__acl__.add((Allow, "group:article", "article_update"))
        acl.__acl__.add((Allow, "group:article", "article_delete"))
        acl.__acl__.add((Allow, "group:article", "article_revert"))
        acl.sync_to_database()

        # Add menu items
        group = MenuGroup("main_menu")
        DBSession.add(Menu("Home", "/", 1, group, Everyone))
        DBSession.add(Menu("Articles", "/article/list", 2, group, Everyone))

        group = MenuGroup("user_area")
        DBSession.add(Menu("Login", "/userarea/login", 1, group,
                           'not_authenticated'))
        DBSession.add(Menu("Recover Password", "/userarea/recover_password",
                           2, group, 'not_authenticated'))
        DBSession.add(Menu("Logout", "/userarea/logout", 3, group,
                           Authenticated))
        DBSession.add(Menu("Register", "/userarea/register", 4, group,
                           'not_authenticated'))
        DBSession.add(Menu("My Profile", "/userarea/profile", 5, group,
                           Authenticated))
        DBSession.add(Menu("Edit Profile", "/userarea/edit", 6, group,
                           Authenticated))
        DBSession.add(Menu("Change Password", "/userarea/change_password",
                           7, group, Authenticated))
        DBSession.add(Menu("User List", "/userarea/list", 8, group,
                           Everyone))

        group = MenuGroup("admin_area")
        DBSession.add(Menu("Edit Menu", "/userarea_admin/edit_menu", 1, group,
                           'edit_menu'))
        DBSession.add(Menu("Edit Menu Groups", "/userarea_admin/edit_menu_group",
                           2, group, 'edit_menu'))
        DBSession.add(Menu("Edit ACL", "/userarea_admin/edit_acl", 3, group,
                           'edit_acl'))
        DBSession.add(Menu("Edit Settings", "/userarea_admin/list_settings",
                           4, group, 'edit_settings'))
        DBSession.add(Menu("Edit CSS", "/userarea_admin/edit_setting/CSS",
                           5, group, 'edit_settings'))
        DBSession.add(Menu("Edit Template", "/userarea_admin/edit_template",
                           6, group, 'edit_settings'))
        DBSession.add(Menu("Upload Files", "/userarea_admin/file_upload",
                           7, group, 'file_upload'))
        DBSession.add(Menu("Backup Articles", "/userarea_admin/backup_articles",
                           8, group, 'backup'))
        DBSession.add(Menu("Restore Articles", 
                           "/userarea_admin/restore_articles", 9, group, 
                           'backup'))
                
        group = MenuGroup("article_not_revision")
        DBSession.add(Menu("Edit", "/article/update/%(page_id)s", 1, group,
                           'article_update'))
        DBSession.add(Menu("Delete", "/article/delete/%(page_id)s", 2, group,
                           'article_delete'))
        DBSession.add(Menu("Switch Renderer [%(renderer)s]",
                           "/article/switch_renderer/%(page_id)s", 3, group,
                           'switch_renderer'))
        DBSession.add(Menu("Make %(private)s",
                           "/article/set_private/%(page_id)s", 4, group,
                           'set_private'))
        DBSession.add(Menu("List Revisions",
                           "/article/list_revisions/%(page_id)s",
                           5, group, 'article_list_revisions'))

        group = MenuGroup("article_revision")
        DBSession.add(Menu("List Revisions",
                           "/article/list_revisions/%(page_id)s", 1, group))
        DBSession.add(Menu("Revert",
                           "/article/revert/%(page_id)s/%(revision)s", 2, group))

        # Add Settings
        DBSession.add(Settings("CSS"))
        DBSession.add(Settings("TITLE", "Untitled Website"))
        DBSession.add(Settings("KEYWORDS"))
        DBSession.add(Settings("DESCRIPTION"))
        DBSession.add(Settings("DEFAULTRENDERER", "HTML"))

        # Add Renderers
        DBSession.add(ArticleRenderers("HTML"))
        DBSession.add(ArticleRenderers("BBCODE"))
        DBSession.add(ArticleRenderers("RESTRUCTUREDTEXT"))
        DBSession.add(ArticleRenderers("MARKDOWN"))