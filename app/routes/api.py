from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.database import get_stats

bp = Blueprint('api', __name__)

@bp.route('/api/stats')
@login_required
def get_stats_endpoint():
    """Get basic statistics about the database"""
    try:
        stats = get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

