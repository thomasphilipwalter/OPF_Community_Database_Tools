from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.database import get_stats, get_database_connection

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

@bp.route('/api/rfp-list')
@login_required
def get_rfp_list():
    """Get list of all RFP metadata entries"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, project_name, organization_group, due_date, country, region, industry
            FROM rfp_metadata 
            ORDER BY created_at DESC
        """)
        
        rfps = []
        for row in cursor.fetchall():
            rfps.append({
                'id': row[0],
                'project_name': row[1] or 'Untitled Project',
                'organization_group': row[2] or 'Unknown Organization',
                'due_date': row[3].isoformat() if row[3] else None,
                'country': row[4] or 'Unknown',
                'region': row[5] or 'Unknown',
                'industry': row[6] or 'Unknown'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'rfps': rfps})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

