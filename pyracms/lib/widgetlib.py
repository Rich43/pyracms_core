from ..deform_schemas.userarea import LoginSchema
from .menulib import MenuLib, MenuGroupNotFound
from .restlib import html_body
from deform.form import Form
from pyramid.security import authenticated_userid, Everyone, has_permission
import postmarkup
import markdown

class WidgetLib():
    def logged_in(self, request):
        return authenticated_userid(request)

    def login_form(self):
        form_instance = Form(LoginSchema(), action="/userarea/login",
                             buttons=('submit',))
        return form_instance

    def merge_res(self, list1, list2, what):
        list1 = set(list1.get_widget_resources()[what])
        if not list2:
            return list1
        return list1 | set(list2)

    def render_article(self, page, article):
        renderer = page.renderer.name
        if renderer == "HTML":
            return article
        elif renderer == "BBCODE":
            return postmarkup.render_bbcode(article)
        elif renderer == "RESTRUCTUREDTEXT":
            return html_body(article)
        elif renderer == "MARKDOWN":
            return markdown.markdown(article)
        
    def generate_menu(self, name, context, request, tmpl_args={}):
        """
        A quite complicated function which generates a list of menu items.
        Each item has certain permissions which may hinder 
        it being displayed.
        """
        def quick_permission(permission):
            """
            A quick way to write all this lot!
            """
            return has_permission(permission, context, request)
        m = MenuLib()
        NOT_AUTH = 'not_authenticated'
        result = []
        try:
            items = m.show_group(name).menu_items
        except MenuGroupNotFound:
            return result
        # Get a list of items in its menu group
        for item in items:
            append = True
            # If the item has any permissions
            if item.permissions:
                # Loop through a comma seperated list of permissions
                for permission in item.permissions.split(","):
                    # Do not append if find not autnenticated permission
                    # (Only triggers when logged in!)
                    if (permission == NOT_AUTH and
                        quick_permission(NOT_AUTH)):
                        append = False
                    # Not sure how this works, wrote it with experimentation
                    if (not quick_permission(permission) and
                        permission != NOT_AUTH and
                        permission != Everyone):
                        append = False
            if append:
                try:
                    result.append([item.url % tmpl_args,
                                   item.name % tmpl_args,
                                   False])
                except KeyError:
                    pass
        if len(result):
            result[-1][-1] = True
        return result
