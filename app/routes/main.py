from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.database import search_database

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Main application page"""
    return render_template('index.html')

@bp.route('/search', methods=['POST'])
@login_required
def search():
    """Search endpoint"""
    try:
        data = request.get_json()
        keywords = data.get('keyword', '').strip()
        source_filters = data.get('source_filters', [])
        experience_filters = data.get('experience_filters', [])
        sustainability_experience_filters = data.get('sustainability_experience_filters', [])
        competencies_filters = data.get('competencies_filters', [])
        sectors_filters = data.get('sectors_filters', [])
        
        results = search_database(keywords, source_filters, experience_filters, sustainability_experience_filters, competencies_filters, sectors_filters)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'keyword': keywords
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})
