'''
Deform Schemas for userarea module.
'''
from ..lib.userlib import UserLib, UserNotFound
from colander import (MappingSchema, SchemaNode, String, Length, Email, All, 
    Invalid, deferred, SequenceSchema, Schema)
from deform.widget import (TextInputWidget, PasswordWidget, CheckedPasswordWidget, 
    HiddenWidget)
from pyramid.security import authenticated_userid, Everyone, Authenticated
u = UserLib()

def valid_username(node, value):
    """ checks to make sure username does not exist """
    def raise_exception():
        raise Invalid(node, 'A user named %s already exists.' % value)
    if value in [Everyone, Authenticated]:
        raise_exception()
    try:
        u.show(value)
    except UserNotFound:
        return
    raise_exception()

class ValidEmail(object):
    """
    Makes sure a user with same email does not exist
    """    
    def __init__(self, request=None):
        self.request = request

    def __call__(self, node, value):
        if self.request:
            user = authenticated_userid(self.request)
            user_obj = u.show(user)
            if user_obj.email_address == value:
                return
        try:
            u.show_by_email(value)
        except UserNotFound:
            return
        raise Invalid(node,
                      'A user with email %s already exists.' % value)

class InvalidEmail(object):
    """
    Makes sure inputted email exists
    """
    def __call__(self, node, value):
        try:
            u.show_by_email(value)
        except UserNotFound:
            raise Invalid(node, 
                          'A user with email %s does not exist.' % value)

@deferred
def deferred_email_validator(node, kw):
    request = kw.get('request')
    return All(Email(), ValidEmail(request))

@deferred
def deferred_default_display_name(node, kw):
    return u.show(kw.get('user')).full_name

@deferred
def deferred_default_email_address(node, kw):
    return u.show(kw.get('user')).email_address

class RecoverPasswordSchema(MappingSchema):
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                   validator=All(Email(), InvalidEmail()))

class RegisterSchema(MappingSchema):
    username = SchemaNode(String(), widget=TextInputWidget(size=40),
                          validator=All(Length(min=3), valid_username))
    display_name = SchemaNode(String(), 
                              widget=TextInputWidget(size=40),
                              validator=Length(min=3))
    password = SchemaNode(
        String(),
        validator=Length(min=8),
        widget=CheckedPasswordWidget(size=40))
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                       validator=All(Email(), ValidEmail()))

class EditUserSchema(MappingSchema):
    display_name = SchemaNode(String(), 
                              widget=TextInputWidget(size=40),
                              validator=Length(min=3),
                              default=deferred_default_display_name)
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                       validator=deferred_email_validator,
                       default=deferred_default_email_address)

class LoginSchema(MappingSchema):
    username = SchemaNode(String(), widget=TextInputWidget(size=40))
    password = SchemaNode(String(), widget=PasswordWidget(size=40))
    redirect_url = SchemaNode(String(), widget=HiddenWidget())
    
class ChangePasswordSchema(MappingSchema):
    password = SchemaNode(
        String(),
        validator=Length(min=8),
        widget=CheckedPasswordWidget(size=20))
    
class UserGroupItem(SequenceSchema):
    name = SchemaNode(String())

class UserGroup(Schema):
    user_group_item = UserGroupItem()
