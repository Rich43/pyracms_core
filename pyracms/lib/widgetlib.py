from datetime import datetime, date, timedelta

from deform.form import Form
from pyramid.security import authenticated_userid, Everyone, has_permission
import markdown
import postmarkup
import pytz
from json import loads
from os.path import splitext

from ..deform_schemas.userarea import LoginSchema
from .helperlib import get_username
from .menulib import MenuLib, MenuGroupNotFound
from .restlib import html_body
from .userlib import UserLib, UserNotFound
from .filelib import FileLib
from .settingslib import SettingsLib

search_html = """
<form action="/redirect/search" method="post" class="searchform">
  <label for="query">Search: </label>
  <input type="text" name="query" />
  <input type="submit" value="Submit" />
</form>
"""

class WidgetLib():
    def __init__(self):
        self.search_html = search_html
        self.bbcode = postmarkup.render_bbcode
        self.splitext = splitext

    def get_gallerylib(self):
        s = SettingsLib()
        if s.has_setting("PYRACMS_GALLERY"):
            from pyracms_gallery.lib.gallerylib import GalleryLib
            return GalleryLib()
        return None

    def get_boardlib(self):
        s = SettingsLib()
        if s.has_setting("PYRACMS_FORUM"):
            from pyracms_forum.lib.boardlib import BoardLib
            return BoardLib()
        return None

    def get_upload_url(self, request):
        return '%s/static/%s/' % (request.host_url, FileLib(request).UPLOAD_DIR)

    def format_time(self, time, request=None, tz='UTC', time_format='%H:%M:%S'):
        """
        Format the time, adjusting with timezone
        """
        u = UserLib()
        try:
            if not request:
                raise UserNotFound
            tz = u.show(get_username(request)).timezone
        except UserNotFound:
            pass
        
        timezone = pytz.timezone(tz)
        usertime = timezone.localize(time)
        time = time.replace(tzinfo=pytz.timezone('UTC'))
        unformatted_time = time + (time - usertime)
        return unformatted_time.strftime(time_format)
    
    def format_date(self, date_obj, request=None, tz='UTC', 
                    date_format='%A %d %b %Y'):
        """
        Format the date, adjusting with timezone
        """
        u = UserLib()
        if isinstance(date_obj, date):
            date_obj = datetime.combine(date_obj, datetime.now().time())
        try:
            if not request:
                raise UserNotFound
            tz = u.show(get_username(request)).timezone
        except UserNotFound:
            pass
        
        timezone = pytz.timezone(tz)
        userdate = timezone.localize(date_obj)
        formatted_date = userdate.strftime(date_format)
        today = datetime.now(timezone)
        yesterday = today - timedelta(days= -1)
        
        if formatted_date == today.strftime(date_format):
            return "Today"
        
        if formatted_date == yesterday.strftime(date_format):
            return "Yesterday"
    
        return formatted_date
    
    def format_date_time(self, date_time, request=None, tz='UTC'):
        """
        Format date and time using above functions
        """
        return "%s %s" % (self.format_date(date_time, request, tz),
                          self.format_time(date_time, request, tz))

    def logged_in(self, request):
        return authenticated_userid(request)

    def login_form(self):
        form_instance = Form(LoginSchema(), action="/userarea/login",
                             buttons=('submit',))
        return form_instance

    def merge_res(self, list1, list2, what):
        if not isinstance(list1, list) or not isinstance(list2, list):
            return []
        list1 = set(list1.get_widget_resources()[what])
        if not list2:
            return list1
        return list1 | set(list2)

    def render_article(self, renderer, article):
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
                # Loop through a comma separated list of permissions
                for permission in item.permissions.split(","):
                    # Do not append if find not authenticated permission
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
                    if item.type == "url":
                        result.append([item.url % tmpl_args,
                                       item.name % tmpl_args,
                                       False])
                    elif item.type == "route":
                        tmpl_args.update(loads(item.route_json))
                        result.append([request.route_url(item.route_name,
                                                         **tmpl_args),
                                       item.name % tmpl_args,
                                       False])
                except KeyError as e:
                    pass
        if len(result):
            result[-1][-1] = True
        return result
