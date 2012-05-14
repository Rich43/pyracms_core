from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url
from pyramid.security import authenticated_userid, Everyone
from deform.form import Form
from deform.exception import ValidationFailure
from colander import null

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

def get_username(request):
    """
    Get the username, otherwise return Everyone
    """
    userid = authenticated_userid(request)
    if userid:
        return userid
    else:
        return Everyone
    
def rapid_deform(context, request, schema, validated_callback=None,
                 appstruct=null, **bind_params):
    """
    Display a deform form. Cache generated forms in database.
    """
    bind_params['request'] = request
    bind_params['context'] = context
    
    # Initialise form library
    bound_schema = schema().bind(**bind_params)
    myform = Form(bound_schema, buttons=['submit'])
    
    # Default template arguments
    reqts = myform.get_widget_resources()
    result = {'js_links': reqts['js'], 'css_links': reqts['css']}
    
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = myform.validate(controls)
        except ValidationFailure as e:
            # Failed validation
            result.update({'form':e.render()})
            return result
        # Form submitted, all validated!
        if validated_callback:
            return validated_callback(context, request, deserialized,
                                      bind_params)
    
    # Add to cache and render.
    form_data = myform.render(appstruct)
    result.update({'form':form_data})
    return result