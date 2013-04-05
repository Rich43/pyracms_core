from ..models import (DBSession, ArticleRevision, ArticlePage, ArticleRenderers, 
    ArticleTags, ArticleVotes)
from .helperlib import serialize_relation
from .searchlib import SearchLib
from .settingslib import SettingsLib
from .taglib import TagLib, ARTICLE
from .userlib import UserLib
from .widgetlib import WidgetLib
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import datetime
import json
import transaction

class RevisionNotFound(Exception):
    pass

class PageNotFound(Exception):
    pass

class PageFound(Exception):
    pass

class AlreadyVoted(Exception):
    pass

class ArticleLib():
    """
    A library to manage the article database.
    """

    def __init__(self):
        self.t = TagLib(ArticleTags, ARTICLE)
        self.s = SearchLib()
        
    def list(self): #@ReservedAssignment
        """
        List all the pages
        """
        pages = DBSession.query(ArticlePage).filter_by(deleted=False)
        if not pages:
            raise PageNotFound
        return [(page.name, page.display_name or page.name) for page in pages]

    def update_article_index(self, request, page, revision, username):
        """
        Update search index
        """
        w = WidgetLib()
        self.s.update_index(page.display_name, 
                            request.route_url("article_read", 
                                              page_id=page.name), 
                            w.render_article(page, revision.article), 
                            self.t.get_tags(page), revision.created, 
                            "article", page.name, username)

    def switch_renderer(self, name):
        page = self.show_page(name)
        renderer_count = DBSession.query(ArticleRenderers).count()
        if page.renderer_id == renderer_count:
            page.renderer_id = 1
            return
        page.renderer_id += 1

    def create(self, request, name, display_name, article, summary, user,
               tags=''):
        """
        Add a new page
        Raise PageFound if page exists
        """
        try:
            self.show_page(name)
            raise PageFound
        except PageNotFound:
            pass
        s = SettingsLib()
        page = ArticlePage(name, display_name)
        revision = ArticleRevision(article, summary, user)
        page.revisions.append(revision)
        default_renderer = s.show_setting("DEFAULTRENDERER").value
        page.renderer = DBSession.query(ArticleRenderers).filter_by(
                                                name=default_renderer).one()
        self.t.set_tags(page, tags)
        self.update_article_index(request, page, revision, user.name)
        DBSession.add(page)

    def update(self, request, page, article, summary, user, tags=''):
        """
        Update a page
        Raise PageNotFound if page does not exist
        """
        if not article:
            self.delete(page, user)
            return
        page.deleted = False
        self.t.set_tags(page, tags)
        revision = ArticleRevision(article, summary, user)
        revision.page = page
        if not page.private:
            self.update_article_index(request, page, revision, user.name)
        DBSession.add(revision)

    def revert(self, request, page, revision, user):
        """
        Revert a page
        Raise PageNotFound if page does not exist
        """
        message = "Reverted revision %s" % revision.id
        self.update(request, page, revision.article, message, user)

    def delete(self, request, page, user):
        """
        Delete a page
        Raise PageNotFound if page does not exist
        """
        revision = ArticleRevision("", "Deleted %s" % page.name, user)
        page.revisions.append(revision)
        page.deleted = True
        self.s.delete_from_index(request.route_url("article_read", 
                                                   page_id=page.name))

    def set_private(self, request, name):
        """
        Flip private switch.
        Raise PageNotFound if page does not exist.
        """
        page = self.show_page(name)
        page.private = not page.private
        self.s.delete_from_index(request.route_url("article_read", 
                                                   page_id=page.name))

    def show_revision(self, page, revision, error=False):
        """
        Get revision objects.
        Raise RevisionNotFound if revision does not exist.
        """
        try:
            return page.revisions.filter_by(id=revision).one()
        except NoResultFound:
            if error:
                raise RevisionNotFound
            else:
                pass

    def show_page(self, name):
        """
        Get page objects.
        Raise PageNotFound if page does not exist.
        """
        try:
            page = DBSession.query(ArticlePage
                                   ).filter(ArticlePage.name.like(name)).one()
        except NoResultFound:
            raise PageNotFound
        return page

    def add_vote(self, db_obj, user, like):
        """
        Add a vote to the database
        """
        
        vote = ArticleVotes(user, like)
        vote.page = db_obj
        try:
            DBSession.add(vote)
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            raise AlreadyVoted

    def to_json(self):
        pages = DBSession.query(ArticlePage)
        items = serialize_relation(pages)
        result = []
        for item in items:
            item['revisions'] = serialize_relation(self.show_page(item["name"]
                                                                  ).revisions)
            result.append(item)
        dthandler = (lambda obj: obj.isoformat() 
                     if isinstance(obj, datetime.datetime) else None)
        return json.dumps(result, default=dthandler)
    
    def from_json(self, request, data):
        u = UserLib()
        data = json.loads(data)
        def convert_date(date):
            date_format = "%Y-%m-%dT%H:%M:%S.%f"
            return datetime.datetime.strptime(date, date_format)
        # Convert the dates back
        for k, dummy in enumerate(data):
            data[k]['created'] = convert_date(data[k]['created'])
            for k2, dummy in enumerate(data[k]['revisions']):
                data[k]['revisions'][k2]['created'] = \
                            convert_date(data[k]['revisions'][k2]['created'])
        # Delete all articles
        for page in DBSession.query(ArticlePage):
            DBSession.delete(page)
            self.s.delete_from_index(request.route_url("article_read", 
                                                page_id=page.name))
        # Add articles back again
        for row in data:
            # Delete revisions and store in memory for later use
            revisions = row['revisions']
            del(row['revisions'])
            # Create page
            page = ArticlePage()
            for k, v in row.items():
                try:
                    setattr(page, k, v)
                except:
                    pass
            # Add revisions
            for row2 in revisions:
                revision = ArticleRevision()
                for k, v in row2.items():
                    try:
                        setattr(revision, k, v)
                    except:
                        pass
                page.revisions.append(revision)
                self.update_article_index(request, page, revision, 
                                          u.show_by_id(revision.user_id).name)
            # Commit changes
            DBSession.add(page)