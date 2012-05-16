from colander import (Schema, SchemaNode, String, 
                      OneOf, SequenceSchema, Integer)
from deform.widget import SelectWidget

class ACLItem(Schema):
    allow_deny = SchemaNode(String(), 
                 widget=SelectWidget(values=[("Allow", "Allow"),
                                             ("Deny", "Deny")],
                 validator=OneOf([("Allow", "Deny")]),
                 default="Allow"))
    who = SchemaNode(String())
    permission = SchemaNode(String())

class ACL(SequenceSchema):
    acl_item = ACLItem()

class EditACL(Schema):
    acl = ACL()
    
class MenuItem(Schema):
    name = SchemaNode(String())
    url = SchemaNode(String())
    permissions = SchemaNode(String())
    position = SchemaNode(Integer())
    
class Menu(SequenceSchema):
    menu_item = MenuItem()

class EditMenuItems(Schema):
    menu = Menu()

class MenuGroupItem(SequenceSchema):
    name = SchemaNode(String())

class MenuGroup(Schema):
    menu_groups = MenuGroupItem()