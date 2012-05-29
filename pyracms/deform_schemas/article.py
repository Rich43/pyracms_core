'''
Deform Schemas for article module.
'''
from colander import MappingSchema, SchemaNode, String, deferred
from deform.widget import TextAreaWidget, TextInputWidget
from ..lib.taglib import ARTICLE, TagLib
t = TagLib(ARTICLE)

@deferred
def deferred_edit_article_default(node, kw):
    if kw.get('page'):
        return kw.get('page').revisions[0].article
    else:
        return ''

@deferred
def deferred_edit_display_name_default(node, kw):
    if kw.get('page'):
        return kw.get('page').display_name
    else:
        return kw.get("page_id")

@deferred
def deferred_edit_tags_default(node, kw):
    if kw.get('page'):
        return t.get_tags(kw.get('page'))
    else:
        return ''
    
class EditArticleSchema(MappingSchema):
    display_name = SchemaNode(String(), widget=TextInputWidget(size=40),
                              default=deferred_edit_display_name_default,
                              missing='')
    article = SchemaNode(String(), 
                         default=deferred_edit_article_default,
                         widget=TextAreaWidget(cols=80, rows=20))
    summary = SchemaNode(String(), widget=TextInputWidget(size=40))
    tags = SchemaNode(String(), widget=TextInputWidget(size=40),
                      missing='', default=deferred_edit_tags_default)