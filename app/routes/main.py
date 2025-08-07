from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.database import search_database, get_user_by_email

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/search', methods=['POST'])
@login_required
def search():
    data = request.get_json()
    keywords = data.get('keyword', '')
    source_filters = data.get('source_filters', [])
    experience_filters = data.get('experience_filters', [])
    sustainability_experience_filters = data.get('sustainability_experience_filters', [])
    competencies_filters = data.get('competencies_filters', [])
    sectors_filters = data.get('sectors_filters', [])

    try:
        results = search_database(
            keywords=keywords,
            source_filters=source_filters,
            experience_filters=experience_filters,
            sustainability_experience_filters=sustainability_experience_filters,
            competencies_filters=competencies_filters,
            sectors_filters=sectors_filters
        )
        return jsonify({'success': True, 'results': results, 'keyword': keywords, 'count': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/user/<email>')
@login_required
def user_page(email):
    """Individual user page showing full result card"""
    try:
        user_data = get_user_by_email(email)
        if not user_data:
            return "User not found", 404
        return render_template('user_page.html', user=user_data)
    except Exception as e:
        return f"Error loading user: {str(e)}", 500
