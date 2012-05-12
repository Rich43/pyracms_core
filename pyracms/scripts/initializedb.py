from ..lib.userlib import UserLib
from ..models import DBSession, Base
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone
from sqlalchemy import engine_from_config
import os
import sys
import transaction

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
        u.create_group("admin", "All Access!", [admin_user])
