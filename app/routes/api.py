from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.database import get_stats
from app.services.rfp_analysis import analyze_rfp_document

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

@bp.route('/analyze-rfp', methods=['POST'])
@login_required
def analyze_rfp():
    """Analyze RFP document and find matching experts"""
    try:
        if 'rfp_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['rfp_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get analysis options
        extract_keywords = request.form.get('extractKeywords', 'true').lower() == 'true'
        find_experts = request.form.get('findExperts', 'true').lower() == 'true'
        
        # Analyze the RFP
        result = analyze_rfp_document(file, extract_keywords, find_experts)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
