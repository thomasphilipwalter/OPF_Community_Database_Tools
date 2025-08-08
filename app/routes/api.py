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
            SELECT id, project_name, organization_group, due_date, country, region, industry, 
                   link, project_focus, opf_gap_size, opf_gaps, deliverables, posting_contact, 
                   potential_experts, project_cost, currency, specific_staffing_needs, created_at
            FROM rfp_metadata 
            ORDER BY created_at DESC
        """)
        
        rfps = []
        for row in cursor.fetchall():
            rfps.append({
                'id': row[0],
                'project_name': row[1] or 'Untitled Project',
                'organization_group': row[2] or '',
                'due_date': row[3].isoformat() if row[3] else None,
                'country': row[4] or '',
                'region': row[5] or '',
                'industry': row[6] or '',
                'link': row[7] or '',
                'project_focus': row[8] or '',
                'opf_gap_size': row[9] or '',
                'opf_gaps': row[10] or '',
                'deliverables': row[11] or '',
                'posting_contact': row[12] or '',
                'potential_experts': row[13] or '',
                'project_cost': row[14],
                'currency': row[15] or '',
                'specific_staffing_needs': row[16] or '',
                'created_at': row[17].isoformat() if row[17] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'rfps': rfps})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

@bp.route('/api/rfp-create', methods=['POST'])
@login_required
def create_rfp():
    """Create a new RFP metadata entry"""
    try:
        data = request.get_json()
        project_name = data.get('project_name', '').strip()
        link = data.get('link', '').strip()
        
        if not project_name:
            return jsonify({'error': 'Project name is required'}), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO rfp_metadata (project_name, link)
            VALUES (%s, %s)
            RETURNING id, project_name, link
        """, (project_name, link))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        new_rfp = {
            'id': result[0],
            'project_name': result[1] or '',
            'organization_group': '',
            'due_date': None,
            'country': '',
            'region': '',
            'industry': '',
            'link': result[2] or ''
        }
        
        return jsonify({'success': True, 'rfp': new_rfp})
        
    except Exception as e:
                             return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/api/document-delete/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    """Delete a specific document"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # First check if the document exists and get its info
        cursor.execute("""
            SELECT id, document_name, rfp_id 
            FROM documents 
            WHERE id = %s
        """, (document_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Document not found'}), 404
        
        document_name = result[1]
        rfp_id = result[2]
        
        # Delete the document
        cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Document "{document_name}" deleted successfully',
            'rfp_id': rfp_id
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/api/documents/<int:rfp_id>', methods=['GET'])
@login_required
def get_documents(rfp_id):
    """Get all documents for a specific RFP"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if RFP exists
        cursor.execute("SELECT id FROM rfp_metadata WHERE id = %s", (rfp_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'RFP not found'}), 404
        
        # Get documents for this RFP
        cursor.execute("""
            SELECT id, document_name, document_text, created_at
            FROM documents 
            WHERE rfp_id = %s 
            ORDER BY created_at DESC
        """, (rfp_id,))
        
        documents = []
        for row in cursor.fetchall():
            # Get first 200 characters of text for preview
            text_preview = row[2][:200] + "..." if len(row[2]) > 200 else row[2]
            
            documents.append({
                'id': row[0],
                'document_name': row[1],
                'document_text': row[2],
                'text_preview': text_preview,
                'created_at': row[3].isoformat() if row[3] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'documents': documents})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/api/document-upload/<int:rfp_id>', methods=['POST'])
@login_required
def upload_document(rfp_id):
    """Upload a document and extract its text"""
    try:
        # Check if RFP exists
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM rfp_metadata WHERE id = %s", (rfp_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'RFP not found'}), 404
        
        # Check if file was uploaded
        if 'document' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx'}
        if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({'error': 'Invalid file type. Please upload PDF, DOC, or DOCX files only.'}), 400
        
        # Extract text from document
        import PyPDF2
        import docx
        import io
        
        document_text = ""
        document_name = file.filename
        
        if file.filename.lower().endswith('.pdf'):
            # Handle PDF files
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                for page in pdf_reader.pages:
                    document_text += page.extract_text() + "\n"
            except Exception as e:
                return jsonify({'error': f'Error reading PDF file: {str(e)}'}), 400
                
        elif file.filename.lower().endswith(('.doc', '.docx')):
            # Handle Word documents
            try:
                doc = docx.Document(io.BytesIO(file.read()))
                for paragraph in doc.paragraphs:
                    document_text += paragraph.text + "\n"
            except Exception as e:
                return jsonify({'error': f'Error reading Word document: {str(e)}'}), 400
        
        # Store in database
        cursor.execute("""
            INSERT INTO documents (rfp_id, document_name, document_text)
            VALUES (%s, %s, %s)
            RETURNING id, document_name, created_at
        """, (rfp_id, document_name, document_text))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'document': {
                'id': result[0],
                'document_name': result[1],
                'created_at': result[2].isoformat() if result[2] else None
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/api/rfp-delete/<int:rfp_id>', methods=['DELETE'])
@login_required
def delete_rfp(rfp_id):
    """Delete an RFP and all its associated documents"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # First check if the RFP exists
        cursor.execute("SELECT id FROM rfp_metadata WHERE id = %s", (rfp_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'RFP not found'}), 404
        
        # Delete the RFP (documents will be deleted automatically due to CASCADE)
        cursor.execute("DELETE FROM rfp_metadata WHERE id = %s", (rfp_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'RFP and all associated documents deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/api/rfp-update/<int:rfp_id>', methods=['PUT'])
@login_required
def update_rfp(rfp_id):
    """Update an existing RFP metadata entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        project_name = data.get('project_name', '').strip()
        if not project_name:
            return jsonify({'error': 'Project name is required'}), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Update the RFP
        cursor.execute("""
            UPDATE rfp_metadata 
            SET project_name = %s, due_date = %s, organization_group = %s, link = %s, 
                country = %s, project_focus = %s, region = %s, industry = %s, 
                opf_gap_size = %s, opf_gaps = %s, deliverables = %s, posting_contact = %s, 
                potential_experts = %s, project_cost = %s, currency = %s, 
                specific_staffing_needs = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, project_name, organization_group, due_date, country, region, industry, 
                     link, project_focus, opf_gap_size, opf_gaps, deliverables, posting_contact, 
                     potential_experts, project_cost, currency, specific_staffing_needs, created_at
        """, (
            project_name,
            data.get('due_date') if data.get('due_date') else None,
            data.get('organization_group', '').strip(),
            data.get('link', '').strip(),
            data.get('country', '').strip(),
            data.get('project_focus', '').strip(),
            data.get('region', '').strip(),
            data.get('industry', '').strip(),
            data.get('opf_gap_size', '').strip(),
            data.get('opf_gaps', '').strip(),
            data.get('deliverables', '').strip(),
            data.get('posting_contact', '').strip(),
            data.get('potential_experts', '').strip(),
            data.get('project_cost') if data.get('project_cost') else None,
            data.get('currency', '').strip(),
            data.get('specific_staffing_needs', '').strip(),
            rfp_id
        ))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'RFP not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        updated_rfp = {
            'id': result[0],
            'project_name': result[1] or '',
            'organization_group': result[2] or '',
            'due_date': result[3].isoformat() if result[3] else None,
            'country': result[4] or '',
            'region': result[5] or '',
            'industry': result[6] or '',
            'link': result[7] or '',
            'project_focus': result[8] or '',
            'opf_gap_size': result[9] or '',
            'opf_gaps': result[10] or '',
            'deliverables': result[11] or '',
            'posting_contact': result[12] or '',
            'potential_experts': result[13] or '',
            'project_cost': result[14],
            'currency': result[15] or '',
            'specific_staffing_needs': result[16] or '',
            'created_at': result[17].isoformat() if result[17] else None
        }
        
        return jsonify({'success': True, 'rfp': updated_rfp})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

