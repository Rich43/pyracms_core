'''
Deform Schemas for userarea module.
'''
from ..lib.userlib import UserLib, UserNotFound
from colander import (MappingSchema, SchemaNode, String, Length, Date, Email, 
    OneOf, All, Invalid, Range, deferred, SequenceSchema, Schema)
from datetime import date, timedelta
from deform.widget import (TextInputWidget, PasswordWidget, CheckedPasswordWidget, 
    TextAreaWidget, SelectWidget, HiddenWidget)
from pyramid.security import authenticated_userid, Everyone, Authenticated
from pytz import all_timezones

all_tz = [(x, x) for x in all_timezones]
u = UserLib()
default_about_me = "I am too lazy to write an 'About Me' :-("

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
def deffered_birthday_validator(node, kw):
    max_date = date.today() - timedelta(days=730)
    return Range(max=max_date, 
                 max_err='${val} is newer than newest date ${max}')

class RecoverPasswordSchema(MappingSchema):
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                       validator=All(Email(), InvalidEmail()))

class RegisterSchema(MappingSchema):
    username = SchemaNode(String(), widget=TextInputWidget(size=40),
                          validator=All(Length(min=3), valid_username))
    full_name = SchemaNode(String(), widget=TextInputWidget(size=40), 
                           validator=Length(min=3))
    password = SchemaNode(String(), validator=Length(min=8),
                          widget=CheckedPasswordWidget(size=40))
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                       validator=All(Email(), ValidEmail()))
    website = SchemaNode(String(), widget=TextInputWidget(size=40), 
                         default="http://www.example.com")
    birthday = SchemaNode(Date(), validator=deffered_birthday_validator)
    about_me = SchemaNode(String(), widget=TextAreaWidget(cols=50, rows=5),
                          default=default_about_me)
    sex = SchemaNode(String(), widget=SelectWidget(values=[["Male"] * 2,
                                                           ["Female"] * 2]),
                     validator=OneOf(["Male", "Female"]))
    timezone = SchemaNode(String(), widget=SelectWidget(values=all_tz, size=20),
                    validator=OneOf(all_timezones), default="Europe/London")

class RegisterAdminSchema(MappingSchema):
    username = SchemaNode(String(), widget=TextInputWidget(size=40),
                          validator=All(Length(min=3), valid_username))
    password = SchemaNode(String(), validator=Length(min=8),
                          widget=CheckedPasswordWidget(size=40))

class EditUserSchema(MappingSchema):
    full_name = SchemaNode(String(), widget=TextInputWidget(size=40),
                           validator=Length(min=3))
    email = SchemaNode(String(), widget=TextInputWidget(size=40), 
                       validator=deferred_email_validator)
    website = SchemaNode(String(), widget=TextInputWidget(size=40))
    birthday = SchemaNode(Date(), validator=deffered_birthday_validator)
    about_me = SchemaNode(String(), widget=TextAreaWidget(cols=50, rows=5))
    sex = SchemaNode(String(), widget=SelectWidget(values=[["Male"] * 2,
                                                           ["Female"] * 2]),
                     validator=OneOf(["Male", "Female"]))
    timezone = SchemaNode(String(), widget=SelectWidget(values=all_tz, size=20),
                          validator=OneOf(all_timezones))

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
