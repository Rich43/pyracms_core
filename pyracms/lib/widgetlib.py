from pyramid.security import authenticated_userid
from ..deform_schemas.userarea import LoginSchema
from deform.form import Form

class WidgetLib():
    def logged_in(self, request):
        return authenticated_userid(request)
    
    def login_form(self):
        form_instance = Form(LoginSchema(), action="/login", 
                             buttons=('submit',))
        return form_instance
    
    def merge_res(self, list1, list2, what):
        list1 = set(list1.get_widget_resources()[what])
        if not list2:
            return list1
        return list1 | set(list2)