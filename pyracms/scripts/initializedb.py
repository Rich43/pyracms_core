from ..lib.userlib import UserLib
from ..models import DBSession, Base
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone, Allow, Authenticated
from sqlalchemy import engine_from_config
import os
import sys
import transaction
from ..models import RootFactory

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
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
        admin_user = u.create_user("admin", "admin@admin.com", "Admin User", 
                                   "admin")
        u.create_user(Everyone, "guest@guest.com", "Guest User", "guest")
    
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
        acl.__acl__.add((Allow, "group:admin", "edit_men"))
        acl.__acl__.add((Allow, "group:admin", "edit_acl"))
        acl.__acl__.add((Allow, "group:article", "group:article"))
        acl.__acl__.add((Allow, "group:article", "article_view"))
        acl.__acl__.add((Allow, "group:article", "article_list"))
        acl.__acl__.add((Allow, "group:article", "article_list_revisions"))
        acl.__acl__.add((Allow, "group:article", "article_create"))
        acl.__acl__.add((Allow, "group:article", "article_update"))
        acl.__acl__.add((Allow, "group:article", "article_delete"))
        acl.__acl__.add((Allow, "group:article", "article_revert"))
        acl.sync_to_database()