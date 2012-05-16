from colander import MappingSchema, SchemaNode, String
from deform.widget import TextInputWidget

class SearchSchema(MappingSchema):
    query = SchemaNode(String(), widget=TextInputWidget())