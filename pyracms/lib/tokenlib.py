from datetime import datetime
from ..models import DBSession, Token, TokenPurpose
from sqlalchemy.orm.exc import NoResultFound

class InvalidToken(Exception):
    pass

class InvalidPurpose(Exception):
    pass

class TokenLib():
    """
    A library to manage tokens.
    Tokens have many uses, password recovery, registration, an api, etc.
    """
    
    def get_purpose(self, purpose):
        """
        Get a token purpose record by its name
        """
        try:
            return DBSession.query(TokenPurpose).filter_by(name=purpose).one()
        except NoResultFound:
            raise InvalidPurpose
        
    def add_token(self, user, purpose):
        """
        Add a token to the database
        """
        t = Token(user, self.get_purpose(purpose))
        DBSession.add(t)
        DBSession.flush()
        return t.name
    
    def delete_expired(self):
        """
        Delete all expired tokens
        """
        now = datetime.now()
        for item in DBSession.query(Token).filter(Token.expires <= now):
            DBSession.delete(item)
    
    def expire_token(self, token):
        """
        Expire a token
        """
        token.expires = datetime(1900,1,1)
        
    def get_token(self, token, expire=True, purpose=None):
        """
        Get a token, raise InvalidToken if missing.
        Tokens are expired on first use by default.
        """
        self.delete_expired()
        try:
            if purpose:
                t = DBSession.query(Token).filter_by(name=token,
                            purpose_id=self.get_purpose(purpose).id).one()
            else:
                t = DBSession.query(Token).filter_by(name=token).one()
            if expire:
                self.expire_token(t)
            return t
        except NoResultFound:
            raise InvalidToken