import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from auth import User

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

def verify_google_token(token):
    """Verify Google ID token and extract user info"""
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Get user info from the token
        user_email = idinfo['email']
        user_name = idinfo.get('name', '')
        user_picture = idinfo.get('picture', '')
        
        # Verify email domain
        if not user_email.endswith('@opf.degree'):
            return None, "Only @opf.degree email addresses are allowed."
        
        return {
            'email': user_email,
            'name': user_name,
            'picture': user_picture
        }, None
        
    except ValueError as e:
        return None, f"Invalid token: {str(e)}"
    except Exception as e:
        return None, f"Authentication error: {str(e)}"

def create_user_from_google_info(user_info):
    """Create User object from Google user info"""
    return User(user_info['email']) 