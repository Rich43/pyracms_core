from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

def redirect(request, route_id, **optargs):
    """
    Quick way to return redirect object
    """
    headers = None
    if "headers" in optargs:
        headers = optargs["headers"]
        del(optargs['headers'])
    if headers:
        return HTTPFound(location=route_url(route_id, request, **optargs),
                         headers=headers)
    else:
        return HTTPFound(location=route_url(route_id, request, **optargs))