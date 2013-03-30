from whoosh.fields import ID, Schema, TEXT, DATETIME, KEYWORD
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser
import os

INDEX_NAME = 'whoosh_index'
schema = Schema(title=TEXT(stored=True), path=ID(stored=True), 
                content=TEXT(stored=True), tags=KEYWORD(stored=True), 
                what=ID(stored=True), created=DATETIME(stored=True), 
                username=ID(stored=True), item_id=ID(stored=True, unique=True))

class SearchLib():
    def __init__(self):
        self.ix = None
        if not exists_in(INDEX_NAME):
            try:
                os.mkdir(INDEX_NAME)
            except:
                pass
            self.ix = create_in(INDEX_NAME, schema)
        else:
            self.ix = open_dir(INDEX_NAME)
    
    def search(self, user_input):
        """
        Execute a search query
        """
        if not user_input:
            return []
        s = self.ix.searcher()
        items = ["title", "tags", "item_id"]
        results = s.search(QueryParser("content", schema).parse(user_input))
        for item in items:
            results.extend(s.search(QueryParser(item, 
                                                schema).parse(user_input)))
        return results
    
    def update_index(self, title, path, content, tags, created, what, item_id, 
                     username, **opt_args):
        """
        Update search index
        """
        writer = self.ix.writer()
        writer.update_document(title=title, path=path, content=content, 
                               tags=tags, created=created, what=what,
                               item_id=item_id, username=username, **opt_args)
        writer.commit()
        
    def delete_from_index(self, path):
        """
        Delete an item from the index
        """
        writer = self.ix.writer()
        writer.delete_by_term('path', path)
        writer.commit()