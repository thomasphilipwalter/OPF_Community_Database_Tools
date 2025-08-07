from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import login_user, logout_user, login_required
from app.utils.auth_utils import get_user_by_email, validate_email
from app.utils.google_auth import verify_google_token, create_user_from_google_info
import os

bp = Blueprint('auth', __name__)

@bp.route('/login')
def login():
    """Login page"""
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    return render_template('login.html', google_client_id=google_client_id)

@bp.route('/verify-google-token', methods=['POST'])
def verify_google_token_route():
    """Verify Google OAuth token and log in user"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 400
        
        # Verify the token and get user info
        user_info, error = verify_google_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Create user object
        user = create_user_from_google_info(user_info)
        
        # Log in the user
        login_user(user)
        
        return jsonify({
            'success': True,
            'user': {
                'email': user.email,
                'name': user_info.get('name', '')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login')) 