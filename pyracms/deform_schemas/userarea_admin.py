from ..models import RootFactory
from colander import (Schema, SchemaNode, String, OneOf, SequenceSchema, Integer, 
    MappingSchema)
from deform import FileData
from deform.widget import SelectWidget, TextAreaWidget, FileUploadWidget
from pyramid.security import Everyone

class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

tmpstore = MemoryTmpStore()

def get_acl(single_result=False):
    rf = RootFactory()
    rf.sync_from_database()
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
    permissions = SchemaNode(String(),
                             widget=SelectWidget(values=get_acl(),
                                                 validator=OneOf(get_acl(True)),
                                                 default=Everyone))
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