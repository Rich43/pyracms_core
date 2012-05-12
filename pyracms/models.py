from hashlib import sha1
from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, synonym
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from sqlalchemy.types import UnicodeText
from zope.sqlalchemy import ZopeTransactionExtension
import os

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class RootFactory(object):
    """
    Default context for views.
    """
    __acl__ = set()
    
    def __init__(self, request=None):
        """
        Load ACL from database if there is none.
        """
        self.request = request
        if len(self.__acl__) == 0:
            self.sync_from_database()

    def sync_from_database(self):
        """
        Load ACL records from database
        """
        rows = DBSession.query(ACL)
        for row in rows:
            self.__acl__.add((row.allow_deny, row.who, row.permission))
        
    def sync_to_database(self):
        """
        Load ACL records into database
        """
        rows = DBSession.query(ACL)
        for row in rows:
            DBSession.delete(row)
        for row in self.__acl__:
            DBSession.add(ACL(row[0], row[1], row[2]))

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

    #}

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
    email_address = Column(Unicode(128), unique=True, nullable=False,
                        info={'rum': {'field':'Email'}})
    _password = Column('password', Unicode(80),
                        info={'rum': {'field':'Password'}}, nullable=False)
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
        salt = sha1()
        salt.update(os.urandom(60))
        sha_hash = sha1()
        sha_hash.update((password + salt.hexdigest()).encode("ascii"))
        password = salt.hexdigest() + sha_hash.hexdigest()
        self._password = password

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    #}

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
        sha_hash = sha1()
        sha_hash.update((password + self.password[:40]).encode("ascii"))
        return self.password[40:] == sha_hash.hexdigest()

class ACL(Base):
    __tablename__ = 'acl'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, autoincrement=True, primary_key=True)
    allow_deny = Column(Unicode(128), index=True)
    who = Column(Unicode(128), index=True)
    permission = Column(Unicode(128), index=True)
    
    def __init__(self, allow_deny, who, permission):
        self.allow_deny = allow_deny
        self.who = who
        self.permission = permission
