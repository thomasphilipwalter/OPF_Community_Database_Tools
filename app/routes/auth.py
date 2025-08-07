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
    next_page = request.args.get('next')
    return render_template('login.html', google_client_id=google_client_id, next_page=next_page)

@bp.route('/verify-google-token', methods=['POST'])
def verify_google_token_route():
    """Verify Google OAuth token and log user in"""
    try:
        data = request.get_json()
        token = data.get('token')
        next_page = data.get('next')
        
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'})
        
        # Verify the token
        user_info, error = verify_google_token(token)
        if error:
            return jsonify({'success': False, 'error': error})
        
        if not user_info:
            return jsonify({'success': False, 'error': 'Invalid token'})
        
        # Get or create user
        user = get_user_by_email(user_info['email'])
        if not user:
            user = create_user_from_google_info(user_info)
        
        # Log user in
        login_user(user)
        
        return jsonify({
            'success': True, 
            'redirect_url': next_page if next_page else '/'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login')) 