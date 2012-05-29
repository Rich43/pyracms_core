from sqlalchemy.orm.exc import NoResultFound
from ..models import DBSession, ArticleRevision, ArticlePage, ArticleRenderers
from .searchlib import update_index, delete_from_index
from .taglib import TagLib, ARTICLE
from .settingslib import SettingsLib

class RevisionNotFound(Exception):
    pass

class PageNotFound(Exception):
    pass

class PageFound(Exception):
    pass

class ArticleLib():
    """
    A library to manage the article database.
    """

    def __init__(self):
        self.t = TagLib(ARTICLE)

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
        update_index(page.display_name, request.route_url("article_read",
                                                          page_id=page.name),
                     revision.article, self.t.get_tags(page),
                     revision.created, "article", page.name, username)

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
        delete_from_index(request.route_url("article_read", page_id=page.name))

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
