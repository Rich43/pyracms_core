from colander import MappingSchema, SchemaNode, String
from deform.widget import TextInputWidget, PasswordWidget

class LoginSchema(MappingSchema):
    username = SchemaNode(String(), widget=TextInputWidget(size=40))
    password = SchemaNode(String(), widget=PasswordWidget(size=40))