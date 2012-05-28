from cgi import escape
from docutils import core, nodes
from docutils.parsers.rst import directives, Directive
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from urllib.parse import quote

CODE = """\
<object type="application/x-shockwave-flash"
        width="%(width)s"
        height="%(height)s"
        class="youtube-embed"
        data="http://www.youtube.com/v/%(yid)s">
    <param name="movie" value="http://www.youtube.com/v/%(yid)s"></param>
    <param name="wmode" value="transparent"></param>
</object>
"""

CODE2 = ("""\
<object width="%(width)s" height="%(height)s" id="flvPlayer">
<param value="true" name="allowfullscreen" />
<param name="allowscriptaccess" value="always" />
<param value="/static/OSplayer.swf" name="movie" />
<param name="flashvars" value="file=%(yid)s" />
<embed width="%(width)s" height="%(height)s" allowscriptaccess="always"
type="application/x-shockwave-flash" allowfullscreen="true"
src="/static/OSplayer.swf"
flashvars="file=%(yid)s" />
</object>
""")

PARAM = """\n    <param name="%s" value="%s"></param>"""

def youtube(name, args, options, content, lineno,
            contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for inserting youtube embedded videos """
    if len(content) == 0:
        return
    string_vars = {
        'yid': quote(content[0]),
        'width': 425,
        'height': 344
        }
    extra_args = content[1:] # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args] # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2] # drop bad lines
    extra_args = dict(extra_args)
    if 'width' in extra_args:
        string_vars['width'] = extra_args.pop('width')
    if 'height' in extra_args:
        string_vars['height'] = extra_args.pop('height')
    return [nodes.raw('', CODE % (string_vars), format='html')]
youtube.content = True
directives.register_directive('youtube', youtube)

def video(name, args, options, content, lineno,
            contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for OSplayer """
    if len(content) == 0:
        return
    string_vars = {
        'yid': quote(content[0]),
        'width': 425,
        'height': 344
        }
    extra_args = content[1:] # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args] # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2] # drop bad lines
    extra_args = dict(extra_args)
    if 'width' in extra_args:
        string_vars['width'] = extra_args.pop('width')
    if 'height' in extra_args:
        string_vars['height'] = extra_args.pop('height')
    return [nodes.raw('', CODE2 % (string_vars), format='html')]
video.content = True
directives.register_directive('video', video)

def gallery(name, args, options, content, lineno,
            contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for lightbox 2 """
    if len(content) == 0:
        return
    string_vars = {
        'url': quote(content[0]),
        'title': "Untitled picture.",
        'thumburl': quote(content[0])
        }
    extra_args = content[1:] # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args] # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2] # drop bad lines
    extra_args = dict(extra_args)
    output = ("""<span class="galleryimage">"""
                """<a href="%s" """) % string_vars['url']

    what = "group"
    if what in extra_args:
        string_vars[what] = escape(extra_args.pop(what))
        output += """rel="lightbox[%s]" """ % string_vars[what]
    else:
        output += """rel="lightbox" """

    what = "title"
    if what in extra_args:
        string_vars[what] = escape(extra_args.pop(what))
        output += """title="%s" """ % string_vars[what]
    else:
        output += """title="%s" """ % string_vars[what]

    what = "thumburl"
    if what in extra_args:
        string_vars[what] = quote(extra_args.pop(what))
        output += """><img src="%s" """ % string_vars[what]
    else:
        output += """><img src="%s" """ % string_vars[what]

    output += """alt="%s" /></a></span>""" % string_vars['title']
    return [nodes.raw('', output, format='html')]
gallery.content = True
directives.register_directive('gallery', gallery)

# Set to True if you want inline CSS styles instead of classes
INLINESTYLES = False

# The default formatter
DEFAULT = HtmlFormatter(noclasses=INLINESTYLES)

# Add name -> formatter pairs for every variant you want to use
VARIANTS = {
    # 'linenos': HtmlFormatter(noclasses=INLINESTYLES, linenos=True),
}

class Pygments(Directive):
    """ Source code syntax hightlighting.
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = dict([(key, directives.flag) for key in VARIANTS])
    has_content = True

    def run(self):
        self.assert_has_content()
        try:
            lexer = get_lexer_by_name(self.arguments[0])
        except ValueError:
            # no lexer found - use the text one instead of an exception
            lexer = TextLexer()
        # take an arbitrary option if more than one is given
        formatter = self.options and VARIANTS[self.options.keys()[0]] or DEFAULT
        parsed = highlight('\n'.join(self.content), lexer, formatter)
        return [nodes.raw('', parsed, format='html')]

directives.register_directive('sourcecode', Pygments)


exampletext = """=========================================
ReStructuredText (rst): plain text markup
=========================================

What is reStructuredText?
~~~~~~~~~~~~~~~~~~~~~~~~~

| blah blah
| blah

cool

| fun
| hehe

.. youtube:: ddojtTIWVPE

.. video:: http://rog.pynguins.com/static/video/Bruce1.flv

.. sourcecode:: python

    for x in range(100):
        print x

Gallery in action
~~~~~~~~~~~~~~~~~

.. gallery:: http://upload.wikimedia.org/wikipedia/commons/b/b8/Pierogi_frying.jpg
    group=mygroup

and another:

.. gallery:: http://upload.wikimedia.org/wikipedia/commons/b/b8/Pierogi_frying.jpg
    group=mygroup


"""

def html_parts(input_string, source_path=None, destination_path=None,
               input_encoding='unicode', doctitle=0, initial_header_level=1):
    """
    Given an input string, returns a dictionary of HTML document parts.

    Dictionary keys are the names of parts, and values are Unicode strings;
    encoding is up to the client.

    Parameters:

    - `input_string`: A multi-line text string; required.
    - `source_path`: Path to the source file or object.  Optional, but useful
      for diagnostic output (system messages).
    - `destination_path`: Path to the file or object which will receive the
      output; optional.  Used for determining relative paths (stylesheets,
      source links, etc.).
    - `input_encoding`: The encoding of `input_string`.  If it is an encoded
      8-bit string, provide the correct encoding.  If it is a Unicode string,
      use "unicode", the default.
    - `doctitle`: Disable the promotion of a lone top-level section title to
      document title (and subsequent section title to document subtitle
      promotion); enabled by default.
    - `initial_header_level`: The initial level for header elements (e.g. 1
      for "<h1>").
    """
    overrides = {'input_encoding': input_encoding,
                 'doctitle_xform': doctitle,
                 'initial_header_level': initial_header_level}
    parts = core.publish_parts(
        source=input_string, source_path=source_path,
        destination_path=destination_path,
        writer_name='html', settings_overrides=overrides)
    return parts

def html_body(input_string, source_path=None, destination_path=None,
              input_encoding='unicode', output_encoding='unicode',
              doctitle=0, initial_header_level=2):
    """
    Given an input string, returns an HTML fragment as a string.

    The return value is the contents of the <body> element.

    Parameters (see `html_parts()` for the remainder):

    - `output_encoding`: The desired encoding of the output.  If a Unicode
      string is desired, use the default value of "unicode" .
    """
    parts = html_parts(
        input_string=input_string, source_path=source_path,
        destination_path=destination_path,
        input_encoding=input_encoding, doctitle=doctitle,
        initial_header_level=initial_header_level)
    fragment = parts['html_body']
    if output_encoding != 'unicode':
        fragment = fragment.encode(output_encoding)
    return fragment

# print html_body(exampletext)