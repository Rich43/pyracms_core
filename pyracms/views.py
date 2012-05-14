from .deform_schemas.article import EditArticleSchema
from .errwarninfo import (INFO_DELETED, INFO, ERROR, ERROR_NOT_FOUND, 
                          INFO_REVERT, ERROR_INVALID_USER_PASS, INFO_LOGIN)
from .lib.articlelib import PageNotFound
from .lib.helperlib import get_username, redirect, rapid_deform
from .lib.userlib import UserLib
from pyracms.deform_schemas.userarea import LoginSchema
from pyracms.errwarninfo import INFO_LOGOUT
from pyracms.lib.articlelib import ArticleLib
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget
from pyramid.url import route_url
from pyramid.view import view_config

u = UserLib()

@view_config(route_name='userarea_login', 
             renderer='userarea/login.jinja2')
def userarea_login(context, request):
    """
    Display login form
    """
    def login_submit(context, request, deserialized, bind_params):
        """
        Submit login form
        """
        username = deserialized.get("username")
        password = deserialized.get("password")
        if u.login(username, password):
            headers = remember(request, username)
            request.session.flash(INFO_LOGIN, INFO)
            return redirect(request, "home", headers=headers)
        else:
            request.session.flash(ERROR_INVALID_USER_PASS, ERROR)
            return redirect(request, "userarea_login")
    return rapid_deform(context, request, LoginSchema, login_submit)
    
@view_config(route_name='userarea_logout')
def userarea_logout(context, request):
    """
    Log the current user out
    """
    headers = forget(request)
    request.session.flash(INFO_LOGOUT, INFO)
    return redirect(request, "home", headers=headers)

@view_config(route_name='css')
def css(request):
    res = request.response
    res.article_type = "text/css"
    res.text = ""
    return res

@view_config(route_name='article_read', renderer='article/article.jinja2', 
             permission='article_view')
@view_config(route_name='article_read_revision', 
             renderer='article/article.jinja2', permission='article_view')
def article_read(context, request):
    """
    Display an article
    """
    c = ArticleLib()
    result = {}
    matchdict_get = request.matchdict.get
    try:
        page = c.show_page(matchdict_get('page_id') or "Front_Page")
        revision = c.show_revision(page, matchdict_get('revision'))
        if page.deleted:
            return HTTPFound(location=route_url("article_update", 
                                                request, page_id=page.name))
        else:
            page.view_count += 1
            result.update({'page': page, 'revision': revision})
            return result
    except PageNotFound:
        return redirect(request, "article_create", 
                        page_id=matchdict_get('page_id'))

@view_config(route_name='article_delete', permission='article_delete')
def article_delete(context, request):
    """
    Delete an article
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        c.delete(request, c.show_page(page_id), u.show(get_username(request)))
        request.session.flash(INFO_DELETED % page_id, INFO)
        return redirect(request, "article_list")
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % page_id, ERROR)
        return redirect(request, "article_list")

@view_config(route_name='article_list', permission='article_list',
             renderer='article/article_list.jinja2')
def article_list(context, request):
    """
    Show a list of articles
    """
    c = ArticleLib()
    return {'pages': c.list()}

@view_config(route_name='article_list_revisions', 
             permission='article_list_revisions', 
             renderer='article/article_list_revisions.jinja2')
def article_list_revisions(context, request):
    """
    Show a list of article revisions, every time a change is made, 
    a revision is added
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        page = c.show_page(page_id)
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % page_id, ERROR)
        return redirect(request, "article_list")
    return {'page': page}

@view_config(route_name='article_update', permission='article_update',
             renderer='article/article_update.jinja2')
def article_update(context, request):
    """
    Display edit article form
    """
    c = ArticleLib()
    def article_update_submit(context, request, deserialized, bind_params):
        """
        Add a article revision to the database
        """
        page = bind_params.get("page")
        name = request.matchdict.get("page_id")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        c.update(request, page, article, summary, 
                 u.show(get_username(request)), tags)
        page.display_name = deserialized.get("display_name")
        return redirect(request, "article_read", page_id=name)
    matchdict_get = request.matchdict.get
    page = c.show_page(matchdict_get('page_id'))
    revision = c.show_revision(page, matchdict_get('revision'))
    return rapid_deform(context, request, EditArticleSchema, 
                        article_update_submit, page=page, 
                        revision=revision, cache=False)

@view_config(route_name='article_create', permission='article_create',
             renderer='article/article_update.jinja2')
def article_create(context, request):
    """
    Display create a new article form
    """
    c = ArticleLib()
    def article_create_submit(context, request, deserialized, bind_params):
        """
        Save new article to the database
        """
        name = request.matchdict.get("page_id")
        display_name = deserialized.get("display_name")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        c.create(request, name, display_name, article, summary, 
                 u.show(get_username(request)), tags)
        return redirect(request, "article_read", page_id=name)
    return rapid_deform(context, request, EditArticleSchema, 
                        article_create_submit,
                        page_id=request.matchdict.get("page_id"))

@view_config(route_name='article_revert', permission='article_revert')
def article_revert(context, request):
    """
    Revert an old revision, basically makes a new revision with old contents
    """
    c = ArticleLib()
    matchdict_get = request.matchdict.get
    try:
        page = c.show_page(matchdict_get('page_id'))
        c.revert(request, page, 
                 c.show_revision(page, matchdict_get('revision')), 
                 u.show(get_username(request)))
        request.session.flash(INFO_REVERT % page.name, INFO)
        return redirect(request, "article_read", page_id=page.name)
    except PageNotFound:
        request.session.flash(ERROR_NOT_FOUND % matchdict_get('page_id'), 
                              ERROR)
        return redirect(request, "article_list")