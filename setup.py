import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'Whoosh',
    'pytz',
    'pyramid_jinja2',
    'postmarkup',
    'docutils',
    'deform',
    'SQLAlchemy',
    'Markdown',
    'Pillow',
    'pyramid_mailer',
    'moviepy',
    'cornice',
    'python-magic'
]

setup(name='pyracms',
      version='0.0',
      description='pyracms',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='pyracms',
      install_requires=requires,
      package_data={"": ['*.jinja2']},
      entry_points="""\
      [paste.app_factory]
      main = pyracms:main
      [console_scripts]
      initialize_pyracms_db = pyracms.scripts.initializedb:main
      """,
      )
