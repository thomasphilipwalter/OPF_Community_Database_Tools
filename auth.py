from flask_login import UserMixin
import re

class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email

def validate_email(email):
    """Validate that email is from @opf.degree domain"""
    if not email:
        return False
    
    # Check if email ends with @opf.degree
    if not email.endswith('@opf.degree'):
        return False
    
    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@opf\.degree$'
    if not re.match(email_pattern, email):
        return False
    
    return True

def get_user_by_email(email):
    """Get user object by email"""
    if validate_email(email):
        return User(email)
    return None 