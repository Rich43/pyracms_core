from ..factory import RootFactory
from ..lib.userlib import UserLib
from ..lib.settingslib import SettingsLib
from ..models import DBSession, Base, Menu, MenuGroup, TokenPurpose
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone, Allow, Authenticated
from sqlalchemy import engine_from_config
from ..lib.menulib import MenuLib
import os
import sys
import transaction

email = "Hello %username.\nYou have recently signed up for $title, "
email += "You need to confirm your $what request"
email += " by clicking the link below:\n$url"

css = """html {
height:100%;
}

body {
background-color:#BDBFCC;
font-family:Arial,Helvetica,sans-serif;
font-size:16px;
height:100%;
margin:0;
padding:0;
}

.header {
text-align: center;
padding: 10px;
margin-left: 20px;
margin-right: 20px;
}

.content {
background-color:#EFF2F8;
border-color:white;
border-style:solid;
border-width:10px 10px 5px;
margin-left:200px;
padding:25px;
min-height: 100px;
border-radius: 25px;
}

.content h2 {
text-align:center;
}

.pageborder {
background-color:white;
margin:20px 30px;
padding-bottom:30px;
border-radius: 15px;
}

.pageborder:after {
clear:both;
content:".";
display:block;
height:0;
visibility:hidden;
}

.menus {
float:left;
height:100%;
width:207px;
}

.menu {
border:1px solid #000000;
margin:10px;
text-align:center;
}

.menu ul li a {
font-weight:bold;
color:black;
height:31px;
line-height:23px;
}

.menu ul li {
width:150px;
}

.menu ul {
list-style-type:none;
padding-left:1em;
}

.menu h3 {
font-size:x-large;
font-weight:normal;
height:15px;
margin-top:0;
width:185px;
}

.redirecthtml {
    padding-bottom: 10px;
}

.error-message {
    color: red;
}

.grid {
width:75%;    
}

.errwarninfoimg {
    padding-left: 20px;
    padding-right: 20px;
}

.errwarninfotext {
    position: absolute;
    top: 25%;
}

.errwarninfodiv {
    margin-top: 20px;
    position: relative;
}

.errwarninfolink {
    padding-left: 20px;
}"""

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
        
        # Default Groups
        u.create_group("admin", "All Access!")
        
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

        # Add Settings
        s = SettingsLib()
        s.create("CSS", css)
        s.create("TITLE", "Untitled Website")
        s.create("KEYWORDS")
        s.create("DESCRIPTION")
        s.create("DEFAULTRENDERER", "HTML")
        s.create("DEFAULTGROUPS", "")
        s.create("RECOVER_PASSWORD", "recover password")
        s.create("RECOVER_PASSWORD_SUBJECT", "Password recovery for %s")
        s.create("REGISTRATION", "registration")
        s.create("EMAIL", email)
        s.create("REGISTRATION_SUBJECT", "Welcome to %s, Please confirm your "
                 + "account.")
        s.create("MAIL_SENDER", "noreply@example.com")
        s.create("INFO_UPDATED", "%s has been updated.")
        s.create("INFO_CREATED", "%s has been created.")
        s.create("INFO_REVERT", "%s was reverted.")
        s.create("INFO_DELETED", "%s was deleted.")
        s.create("INFO_LOGIN", "You have been logged in.")
        s.create("INFO_LOGOUT", "You have been logged out.")
        s.create("INFO_PASS_CHANGE", "Your password has been changed.")
        s.create("INFO_ACTIVATON_EMAIL_SENT", "An activation email has been "
                 + "sent to %s.")
        s.create("INFO_RECOVERY_EMAIL_SENT", "An password recovery email has "
                 + "been sent to %s.")
        s.create("INFO_ACC_UPDATED", "Your account information has been updated.")
        s.create("INFO_ACC_CREATED", "Your account has been activated.")
        s.create("INFO_MENU_UPDATED", "The menu (%s) has been updated.")
        s.create("INFO_MENU_GROUP_UPDATED", "The list of menu groups has " +
                                            "been updated.")
        s.create("INFO_ACL_UPDATED", "The access control list has been updated.")
        s.create("INFO_VOTE", "Your vote has been added.")
        s.create("ERROR_FOUND", "%s already exists.")
        s.create("ERROR_NOT_FOUND", "%s was not found.")
        s.create("ERROR_INVALID_USER_PASS", "Invalid username or password.")
        s.create("ERROR_TOKEN", "Token could not be found.")
        s.create("ERROR_VOTE", "You have already voted.")

        # Add menu items
        m = MenuLib()
        group = m.add_group("main_menu")
        m.add_menu_item_route("Home", "home", 1, group, Everyone)
        
        group = m.add_group("user_area")
        m.add_menu_item_route("Login", "userarea_login", 1, group,
                              'not_authenticated')
        m.add_menu_item_route("Recover Password", "userarea_recover_password",
                              2, group, 'not_authenticated')
        m.add_menu_item_route("Logout", "userarea_logout", 3, group,
                              Authenticated)
        m.add_menu_item_route("Register", "userarea_register", 4, group,
                              'not_authenticated')
        m.add_menu_item_route("My Profile", "userarea_profile", 5, group,
                              Authenticated)
        m.add_menu_item_route("Edit Profile", "userarea_edit", 6, group,
                              Authenticated)
        m.add_menu_item_route("Change Password", "userarea_change_password",
                              7, group, Authenticated)
        m.add_menu_item_route("User List", "userarea_list", 8, group,
                              Everyone)
        
        group = m.add_group("admin_area")
        m.add_menu_item_route("Edit Menu", "userarea_admin_edit_menu",
                              1, group, 'edit_menu')
        m.add_menu_item_route("Edit Menu Groups",
                              "userarea_admin_edit_menu_group",
                              2, group, 'edit_menu')
        m.add_menu_item_route("Edit ACL", "userarea_admin_edit_acl",
                              3, group, 'edit_acl')
        m.add_menu_item_route("Edit Settings", "userarea_admin_list_settings",
                              4, group, 'edit_settings')
        m.add_menu_item_route("Edit CSS", "userarea_admin_edit_settings",
                              5, group, 'edit_settings', {"name": "CSS"})
        m.add_menu_item_route("Edit Template", "userarea_admin_edit_template",
                              6, group, 'edit_settings')
        m.add_menu_item_route("Upload Files", "userarea_admin_file_upload",
                              7, group, 'file_upload')
        m.add_menu_item_route("Backup Menus", "userarea_admin_backup",
                              10, group, 'backup', {"what": "menus"})
        m.add_menu_item_route("Restore Menus", "userarea_admin_restore",
                              11, group, 'backup', {"what": "menus"})
        m.add_menu_item_route("Backup Settings", "userarea_admin_backup",
                              12, group, 'backup', {"what": "settings"})
        m.add_menu_item_route("Restore Settings", "userarea_admin_restore",
                              13, group, 'backup', {"what": "settings"})
        m.add_menu_item_route("Manage Users", "userarea_admin_manage_users",
                              14, group, 'group:admin')

        DBSession.add(TokenPurpose("register"))
        DBSession.add(TokenPurpose("password_recovery"))