from .models import DBSession, User

def groupfinder(userid, request):
    if request.session.get('groupfinder'):
        if request.session['groupfinder'].get(userid):
            return request.session['groupfinder'][userid]
    else:
        request.session['groupfinder'] = {}
    auth = DBSession.query(User).filter(User.name==userid).first()
    if auth:
        result = [('group:%s' % group.name) for group in auth.groups]
        request.session['groupfinder'][userid] = result
        return result