from ..factory import RootFactory
from ..models import DBSession
from .userarea import EditUserSchema
from colander import (Schema, SchemaNode, String, OneOf, SequenceSchema, Integer, 
    MappingSchema, deferred, Boolean, Set)
from deform import FileData
from deform.widget import SelectWidget, TextAreaWidget, FileUploadWidget
from pyramid.security import Everyone
from ..lib.userlib import UserLib

class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

tmpstore = MemoryTmpStore()

def get_acl(single_result=False):
    rf = RootFactory(session=DBSession)
    result = []
    for item in rf.__acl__:
        if item != Everyone:
            if single_result:
                result.append(item[2])
            else:
                result.append((item[2], item[2]))
    if single_result:
        result.insert(0, Everyone)
    else:
        result.insert(0, (Everyone, Everyone))
    return result

@deferred
def deferred_acl_widget(node, kw):
    return SelectWidget(values=get_acl())

@deferred
def deferred_acl_validator(node, kw):
    return OneOf(get_acl(True))

class ACLItem(Schema):
    allow_deny = SchemaNode(String(),
                 widget=SelectWidget(values=[("Allow", "Allow"),
                                             ("Deny", "Deny")],
                 validator=OneOf([("Allow", "Deny")]),
                 default="Allow"))
    who = SchemaNode(String())
    permission = SchemaNode(String(), widget=deferred_acl_widget,
                            validator=deferred_acl_validator, 
                            default=Everyone)

class ACL(SequenceSchema):
    acl_item = ACLItem()

class EditACL(Schema):
    acl = ACL()

@deferred
def deferred_group_widget(node, kw):
    return SelectWidget(values=[(x[0], x[0]) 
                                for x in UserLib().list_groups()], 
                        multiple=True)

class MenuItem(Schema):
    name = SchemaNode(String())
    url = SchemaNode(String())
    permissions = SchemaNode(String(), widget=deferred_acl_widget,
                             validator=deferred_acl_validator, 
                             default=Everyone)
    position = SchemaNode(Integer())
    
class Menu(SequenceSchema):
    menu_item = MenuItem()

class EditMenuItems(Schema):
    menu = Menu()

class MenuGroupItem(SequenceSchema):
    name = SchemaNode(String())

class MenuGroup(Schema):
    menu_groups = MenuGroupItem()

class SettingSchema(MappingSchema):
    value = SchemaNode(String(), widget=TextAreaWidget(cols=140, rows=20))

class RestoreBackupSchema(Schema):
    restore_backup_json_file = SchemaNode(FileData(), 
                                          widget=FileUploadWidget(tmpstore))

class RestoreSettingsSchema(Schema):
    restore_settings_json_file = SchemaNode(FileData(), 
                                            widget=FileUploadWidget(tmpstore))
    
class EditAdminUserSchema(EditUserSchema):
    banned = SchemaNode(Boolean())
    password = SchemaNode(String(), missing='')
    groups = SchemaNode(Set(), widget=deferred_group_widget)
