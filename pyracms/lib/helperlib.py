from colander import null
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid, Everyone
from pyramid.url import route_url
import inspect

def is_int(data):
    try:
        int(data)
    except ValueError:
        return False
    return True

def display_json(request, json):
    res = request.response
    res.content_type = "application/json"
    res.text = json
    return res

def list_routes(request, show_pattern=False):
    for item in request.registry.introspector.get_category('routes'):
        if len(item["related"]):
            name = item["related"][0].discriminator[3]
            if not name.startswith("__"):
                if show_pattern:
                    intro = request.registry.introspector.get('routes', name)
                    yield (str(name), str(intro['pattern']))
                else:
                    yield name

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
                 appstruct=null, action='', use_ajax=False,
                 form_name='form', submit_name='submit', **bind_params):
    """
    Display a deform form. Cache generated forms in database.
    """
    bind_params['request'] = request
    bind_params['context'] = context

    # Initialise form library
    bound_schema = schema().bind(**bind_params)
    myform = Form(bound_schema, action=action, use_ajax=use_ajax,
                  buttons=[submit_name])

    # Default template arguments
    reqts = myform.get_widget_resources()
    reqts['js'] = [x.replace("deform:static/", "") for x in reqts['js']]
    reqts['css'] = [x.replace("deform:static/", "") for x in reqts['css']]
    result = {'js_links': reqts['js'], 'css_links': reqts['css']}

    if submit_name.replace(" ", "_") in request.POST:
        controls = list(request.POST.items())
        try:
            deserialized = myform.validate(controls)
        except ValidationFailure as e:
            # Failed validation
            result.update({form_name:e.render()})
            return result
        # Form submitted, all validated!
        if validated_callback:
            return validated_callback(context, request, deserialized,
                                      bind_params)

    # Add to cache and render.
    form_data = myform.render(bind_params)
    result.update({form_name: form_data})
    result.update(bind_params)
    return result

def serialize_relation(obj):
    """
    Serialize a relationship into a list of dictionaries.
    """
    return [{k:v for k, v in x.__dict__.items() if not k.startswith("_")}
            for x in obj]

def deserialize_relation(l, obj, extra_vars={}):
    """
    Deserialize a serialized relationship
    """
    result = []
    for d in l:
        init_keys = []
        if hasattr(obj, "__init__"):
            init_keys = set(inspect.getargspec(obj.__init__).args)
            init_keys = init_keys - set(["self"])
        s = set(d.keys()) - set(init_keys) - set(["id"])
        init_dict = {}
        for key in init_keys:
            if hasattr(obj, key) and key in d:
                init_dict[key] = d[key]
        init_dict.update(extra_vars)
        obj_inst = obj(**init_dict)
        for key in s:
            setattr(obj_inst, key, d[key])
        result.append(obj_inst)
    return result
    
def dict_to_acl(item):
    """
    Convert (converted) dictionary ACL to normal tuple format
    """
    return (item['allow_deny'], item['who'], item['permission'])

def acl_to_dict(item):
    """
    Convert standard tuple ACL format to a dictionary
    """
    return {'allow_deny': item[0], 'who': item[1], 'permission': item[2]}
