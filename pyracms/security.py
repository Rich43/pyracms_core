from .models import DBSession, User

def groupfinder(userid, request):
    auth = DBSession.query(User).filter(User.name==userid).first()
    if auth:
        return [('group:%s' % group.name) for group in auth.groups]