from ..models import DBSession, User, Group
from sqlalchemy.orm.exc import NoResultFound
import json
from .settingslib import SettingsLib

class UserNotFound(Exception):
    pass

class GroupNotFound(Exception):
    pass

class UserLib():
    """
    A library to manage the user database.
    """
    
    def show(self, name):
        """
        Get a user from his username
        Raise UserNotFound if user does not exist
        """
        
        if not name:
            raise UserNotFound
        
        try:
            return DBSession.query(User).filter_by(name=name).one()
        except NoResultFound:
            raise UserNotFound
    
    def show_by_email(self, email):
        """
        Get a user from his email
        Raise UserNotFound if user does not exist
        """
        
        if not email:
            raise UserNotFound
        
        try:
            return DBSession.query(User).filter_by(email_address=email).one()
        except NoResultFound:
            raise UserNotFound
    
    def show_by_id(self, user_id):
        """
        Get a user from his database id
        Raise UserNotFound if user does not exist
        """
        try:
            return DBSession.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserNotFound

    def show_by_token(self, token):
        """
        Get a user from his token
        Raise UserNotFound if user does not exist
        """
        try:
            return DBSession.query(User).filter_by(api_uuid=token).one()
        except NoResultFound:
            raise UserNotFound

    def list(self, first=True, as_obj=False):
        """
        List all the users
        """
        if as_obj:
            return DBSession.query(User)
        if first:
            return [x[0] for x in DBSession.query(User.name).all()]
        else:
            return DBSession.query(User.name, User.full_name).all()

    def list_groups(self, as_obj=False):
        """
        List all the groups
        """
        if as_obj:
            return DBSession.query(Group)
        else:
            return DBSession.query(Group.name, Group.display_name).all()

    def exists(self, name):
        """
        Check to see if a user exists
        Return True/False
        """
        try:
            DBSession.query(User).filter_by(name=name).one()
        except NoResultFound:
            return False
        
        return True
    
    def login(self, username, password):
        """
        Validate username and password.
        """
        try:
            user = self.show(username)
        except UserNotFound:
            return False
        if user.banned:
            return False
        return user.validate_password(password)
    
    def change_password(self, username, password):
        """
        Validate username and change password.
        """
        user = self.show(username)
        user.password = password

    def show_group(self, name):
        """
        Get a group from its groupname
        Raise GroupNotFound if group does not exist
        """
        try:
            grp = DBSession.query(Group).filter_by(name=name).one()
        except NoResultFound:
            raise GroupNotFound
        
        if not name:
            raise GroupNotFound
        
        return grp

    def create_user(self, name, full_name, email_address, password, sex):
        """
        Create a user. Returns the user object.
        """
        user = User(name)
        user.email_address = email_address
        user.full_name = full_name
        user.password = password
        user.sex = sex

        DBSession.add(user)
        return user
    
    def update_user(self, name, full_name, email_address):
        """
        Update a user. Returns the user object.
        """
        user = self.show(name)
        user.email_address = email_address
        user.full_name = full_name
        return user
    
    def delete_user(self, name):
        """
        Delete a user.
        """
        user = self.show(name)
        DBSession.delete(user)
        
    def create_group(self, group_name, display_name, users=[]):
        """
        Create a group. Returns the group object.
        """
        group = Group()
        group.name = group_name
        group.display_name = display_name
        for user in users:
            user.groups.append(group)
        DBSession.add(group)
        return group

    def list_users_groups(self, user_name):
        """
        List all of the users groups
        :param user_name: User's username
        :return: List of groups
        """
        return [x.name for x in self.show(user_name).groups]

    def list_users_permissions(self, user_name):
        """
        List all of the users permissions
        :param user_name: User's username
        :return: List of permissions
        """
        groups = self.list_users_groups(user_name)
        s = SettingsLib()
        ACLs = json.loads(s.show_setting("ACL"))
        result = []
        for ACL in ACLs:
            for group in groups:
                if "group:" + group == ACL[1] and ACL[0].lower() == "allow":
                    result.append(ACL[2])
        return result

    def count(self):
        return self.list(as_obj=True).count()