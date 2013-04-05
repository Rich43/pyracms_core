from ..factory import RootFactory
from ..lib.userlib import UserLib
from ..models import DBSession, Base, Menu, MenuGroup, Settings, Sexes
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone, Allow, Authenticated
from sqlalchemy import engine_from_config
import os
import sys
import transaction

email = "Hello %username.\nYou have recently signed up for $title, "
email += "You need to confirm your $what request"
email += " by clicking the link below:\n$url"

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
        # Add Sexes
        male = Sexes("Male")
        female = Sexes("Female")
        DBSession.add(male)
        DBSession.add(female)
        
        # Default Users
        u = UserLib()
        admin_user = u.create_user("admin", "Admin User", "admin@admin.com",
                                   "admin", "Male")
        u.create_user(Everyone, "Guest User", "guest@guest.com", "guest",
                      "Female")
        
        # Default Groups
        u.create_group("admin", "All Access!", [admin_user])
        
        # Default ACL
        acl = RootFactory(session=DBSession)
        acl.__acl__.append((Allow, Everyone, Everyone))
        acl.__acl__.append((Allow, Authenticated, Authenticated))
        acl.__acl__.append((Allow, Authenticated, "not_authenticated"))
        acl.__acl__.append((Allow, Authenticated, "userarea_edit"))
        acl.__acl__.append((Allow, Authenticated, 'vote'))
        acl.__acl__.append((Allow, "group:admin", "group:admin"))
        acl.__acl__.append((Allow, "group:admin", "edit_menu"))
        acl.__acl__.append((Allow, "group:admin", "edit_acl"))
        acl.__acl__.append((Allow, "group:admin", "edit_settings"))
        acl.__acl__.append((Allow, "group:admin", "file_upload"))
        acl.__acl__.append((Allow, "group:admin", "backup"))
        
        # Add menu items
        group = MenuGroup("main_menu")
        DBSession.add(Menu("Home", "/", 1, group, Everyone))
        
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
        DBSession.add(Menu("Edit Menu", "/userarea_admin/edit_menu", 
                           1, group, 'edit_menu'))
        DBSession.add(Menu("Edit Menu Groups", 
                           "/userarea_admin/edit_menu_group", 
                           2, group, 'edit_menu'))
        DBSession.add(Menu("Edit ACL", "/userarea_admin/edit_acl", 
                           3, group, 'edit_acl'))
        DBSession.add(Menu("Edit Settings", "/userarea_admin/list_settings",
                           4, group, 'edit_settings'))
        DBSession.add(Menu("Edit CSS", "/userarea_admin/edit_setting/CSS",
                           5, group, 'edit_settings'))
        DBSession.add(Menu("Edit Template", "/userarea_admin/edit_template",
                           6, group, 'edit_settings'))
        DBSession.add(Menu("Upload Files", "/userarea_admin/file_upload",
                           7, group, 'file_upload'))
        DBSession.add(Menu("Backup Settings", "/userarea_admin/backup_settings",
                           10, group, 'backup'))
        DBSession.add(Menu("Restore Settings", 
                           "/userarea_admin/restore_settings", 
                           11, group, 'backup'))
        
        # Add Settings
        def add_dict(d):
            for k, v in d.items():
                if not v:
                    DBSession.add(Settings(k))
                else:
                    DBSession.add(Settings(k, v))
        d = {"CSS": ".menu {float: left;}\n.searchform {float: right;}", 
             "TITLE": "Untitled Website",
             "KEYWORDS": None, "DESCRIPTION": None, "DEFAULTRENDERER": "HTML",
             "RECOVER_PASSWORD": "recover password", 
             "RECOVER_PASSWORD_SUBJECT": "Password recovery for %s", 
             "REGISTRATION": "registration", "EMAIL": email,
             "REGISTRATION_SUBJECT": 
             "Welcome to %s, Please confirm your account.", 
             "MAIL_SENDER": "noreply@example.com",
             "INFO_UPDATED": "%s has been updated.",
             "INFO_CREATED": "%s has been created.",
             "INFO_REVERT": "%s was reverted.",
             "INFO_DELETED": "%s was deleted.",
             "INFO_LOGIN": "You have been logged in.",
             "INFO_LOGOUT": "You have been logged out.",
             "INFO_PASS_CHANGE": "Your password has been changed.",
             "INFO_ACTIVATON_EMAIL_SENT": 
             "An activation email has been sent to %s.",
             "INFO_RECOVERY_EMAIL_SENT": 
             "An password recovery email has been sent to %s.",
             "INFO_ACC_UPDATED": "Your account information has been updated.",
             "INFO_ACC_CREATED": "Your account has been activated.",
             "INFO_MENU_UPDATED": "The menu (%s) has been updated.",
             "INFO_MENU_GROUP_UPDATED": 
             "The list of menu groups has been updated.",
             "INFO_FORUM_CATEGORY_UPDATED": 
             "The list of forum categories has been updated.",
             "INFO_ACL_UPDATED": "The access control list has been updated.",
             "INFO_VOTE": "Your vote has been added.",
             "ERROR_NOT_FOUND": "%s was not found.",
             "ERROR_INVALID_USER_PASS": "Invalid username or password.",
             "ERROR_TOKEN": "Token could not be found.",
             "ERROR_VOTE": "You have already voted."}
        add_dict(d)