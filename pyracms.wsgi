from pyramid.paster import get_app
import os
from os.path import join
application = get_app(
  join(os.getcwd(), production.ini), 'main')

