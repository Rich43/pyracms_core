from datetime import datetime, timedelta
from sqlalchemy import (Column, Integer, Unicode, desc, UnicodeText, DateTime, 
    Boolean, BigInteger, LargeBinary, Date)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship, synonym, 
    deferred)
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from zope.sqlalchemy import ZopeTransactionExtension
import hashlib
import uuid

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class UserGroup(Base):
    """
    This is the association table for the many-to-many relationship between
    groups and members - this is, the memberships.
    It's required by repoze.what.
    """
    __tablename__ = 'user_group'
    __table_args__ = (UniqueConstraint('user_id', 'group_id'),
                        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

class Group(Base):
    """
    Group definition for :mod:`repoze.what`.
    Only the ``name`` column is required by :mod:`repoze.what`.
    """

    __tablename__ = 'group'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True, nullable=False)
    display_name = Column(Unicode(128), nullable=False)

    #{ Special methods

    def __repr__(self):
        return '<Group: name=%r>' % self.name

    def __unicode__(self):
        return self.name

class FilesData(Base):
    __tablename__ = 'filesdata'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    data = deferred(Column(LargeBinary(10 ** 6), nullable=False))

    def __init__(self, data):
        self.data = data

class Files(Base):
    __tablename__ = 'files'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, nullable=False)
    mimetype = Column(Unicode(128), index=True, nullable=False)
    size = Column(BigInteger, index=True, default=0)
    created = Column(DateTime, default=datetime.now)
    upload_complete = Column(Boolean, default=False, index=True)
    download_count = Column(Integer, default=0, index=True)
    data = relationship(FilesData,
                    cascade="all, delete, delete-orphan", single_parent=True)
    def __init__(self, name, mimetype):
        self.name = name
        self.mimetype = mimetype

class Sexes(Base):
    __tablename__ = 'sexes'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(6), index=True, unique=True, nullable=False)
    def __init__(self, name):
        self.name = name

# The 'info' argument we're passing to the email_address and password columns
# contain metadata that Rum (http://python-rum.org/) can use generate an
# admin interface for your models.
class User(Base):
    """
    User definition.

    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``name`` column.

    """
    __tablename__ = 'user'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    #{ Columns

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True, nullable=False)
    full_name = Column(Unicode(128), nullable=False)
    email_address = Column(Unicode(128), unique=True, nullable=False)
    website = Column(Unicode(128), default='')
    birthday = Column(Date, default=datetime.date(datetime.now()))
    sex_id = Column(Integer, ForeignKey('sexes.id'), nullable=False)
    sex = relationship(Sexes, uselist=False)
    aboutme = Column(UnicodeText, default='')
    created = Column(DateTime, default=datetime.now)
    banned = Column(Boolean, default=True)
    timezone = Column(Unicode(16), nullable=False, default="Europe/London")
    file_id = Column(Integer, ForeignKey('files.id'))
    file_obj = relationship(Files, cascade="all, delete")
    _password = Column('password', Unicode(128), nullable=False)
    groups = relationship('Group', secondary=UserGroup.__table__,
                          backref='user')

    #{ Special methods
    def __init__(self, name):
        self.name = name

    #{ Getters and setters

    @classmethod
    def by_email_address(cls, email):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter(cls.email_address == email).first()

    @classmethod
    def by_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter(cls.name == username).first()

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        self._password = hashlib.sha512(password.encode()).hexdigest()

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))
    
    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        password = hashlib.sha512(password.encode()).hexdigest()
        return self.password == password

class Settings(Base):
    __tablename__ = 'settings'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True, nullable=False)
    value = Column(UnicodeText)

    def __init__(self, name, value=""):
        self.name = name
        self.value = value

class ArticleTags(Base):
    __tablename__ = 'articletags'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, nullable=False)
    page_id = Column(Integer, ForeignKey('articlepage.id'))
    page = relationship("ArticlePage")

    def __init__(self, name):
        self.name = name

class ArticleRevision(Base):
    __tablename__ = 'articlerevision'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('articlepage.id'), nullable=False)
    article = Column(UnicodeText, default='')
    summary = Column(Unicode(128), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)
    page = relationship("ArticlePage")
    created = Column(DateTime, default=datetime.now)

    def __init__(self, article="", summary="", user=None):
        self.article = article
        self.summary = summary
        if user:
            self.user = user

class ArticleRenderers(Base):
    __tablename__ = 'articlerenderers'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

class ArticlePage(Base):
    __tablename__ = 'articlepage'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, nullable=False)
    created = Column(DateTime, default=datetime.now)
    deleted = Column(Boolean, default=False, index=True)
    private = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0, index=True)
    renderer_id = Column(Integer, ForeignKey('articlerenderers.id'),
                         nullable=False, default=1)
    revisions = relationship(ArticleRevision,
                             cascade="all, delete, delete-orphan",
                             lazy="dynamic",
                             order_by=desc(ArticleRevision.created))
    tags = relationship(ArticleTags, cascade="all, delete, delete-orphan")
    renderer = relationship(ArticleRenderers)

    def __init__(self, name="", display_name=""):
        self.name = name
        self.display_name = display_name

class Menu(Base):
    __tablename__ = 'menu'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('menugroup.id'), nullable=False)
    group = relationship("MenuGroup")
    position = Column(Integer, default=1, nullable=False)
    url = Column(Unicode(128), nullable=False)
    name = Column(Unicode(128), nullable=False)
    permissions = Column(Unicode(128), default='')

    def __init__(self, name, url, position, group, permissions=''):
        self.name = name
        self.url = url
        self.position = position
        self.group = group
        self.permissions = permissions

class MenuGroup(Base):
    __tablename__ = 'menugroup'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)
    menu_items = relationship(Menu, order_by=Menu.position,
                              cascade="all, delete, delete-orphan")

    def __init__(self, name):
        self.name = name

def gen_token():
    return str(uuid.uuid4())

def expire_time():
    return datetime.now() + timedelta(hours=24)

class TokenPurpose(Base):
    __tablename__ = 'tokenpurpose'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

class Token(Base):
    __tablename__ = 'token'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True,
                  default=gen_token, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)
    purpose_id = Column(Integer, ForeignKey('tokenpurpose.id'),
                        nullable=False)
    purpose = relationship(TokenPurpose)
    created = Column(DateTime, default=datetime.now)
    expires = Column(DateTime, default=expire_time)

    def __init__(self, user, purpose):
        self.user = user
        self.purpose = purpose

class ArticleVotes(Base):
    __tablename__ = 'articlevotes'
    __table_args__ = (UniqueConstraint('user_id', 'page_id'),
                      {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('articlepage.id'))
    page = relationship("ArticlePage")
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("User")
    like = Column(Boolean, nullable=False, index=True)

    def __init__(self, user, like):
        self.user = user
        self.like = like
