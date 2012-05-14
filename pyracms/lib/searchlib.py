from whoosh.fields import ID, Schema, TEXT, DATETIME, NUMERIC
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
import os

INDEX_NAME = 'whoosh_index'
schema = Schema(title=TEXT(stored=True), path=ID(stored=True), 
                content=TEXT, tags=TEXT(stored=True), what=TEXT(stored=True), 
                created=DATETIME(stored=True), expired=DATETIME(stored=True),
                category=TEXT(stored=True), region=TEXT(stored=True),
                budget=NUMERIC(stored=True), username=TEXT(stored=True),
                item_id=TEXT(stored=True))

if not os.path.exists(INDEX_NAME):
    os.mkdir(INDEX_NAME)
    WIX = create_in(INDEX_NAME, schema)
else:
    WIX = open_dir(INDEX_NAME)
    
def search(user_input):
    """
    Execute a search query
    """
    if not user_input:
        return []
    searcher = WIX.searcher()
    query = QueryParser("content", WIX.schema).parse(user_input)
    return searcher.search(query)

def update_index(title, path, content, tags, created, what, item_id, 
                 username, **opt_args):
    """
    Update search index
    """
    writer = WIX.writer()
    writer.update_document(title=title, path=path, content=content, 
                           tags=tags, created=created, what=what,
                           item_id=item_id, username=username, **opt_args)
    writer.commit()
    
def delete_from_index(path):
    """
    Delete an item from the index
    """
    writer = WIX.writer()
    writer.delete_by_term('path', path)
    writer.commit()