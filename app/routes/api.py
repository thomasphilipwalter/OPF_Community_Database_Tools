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
                   potential_experts, project_cost, currency, specific_staffing_needs, created_at,
                   ai_fit_assessment, ai_competitive_position, ai_key_strengths, ai_gaps_challenges,
                   ai_resource_requirements, ai_risk_assessment, ai_recommendations, ai_analysis_date
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
                'created_at': row[17].isoformat() if row[17] else None,
                'ai_fit_assessment': row[18] or '',
                'ai_competitive_position': row[19] or '',
                'ai_key_strengths': row[20] or '',
                'ai_gaps_challenges': row[21] or '',
                'ai_resource_requirements': row[22] or '',
                'ai_risk_assessment': row[23] or '',
                'ai_recommendations': row[24] or '',
                'ai_analysis_date': row[25].isoformat() if row[25] else None
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

@bp.route('/api/ai-analyze/<int:rfp_id>', methods=['POST'])
@login_required
def ai_analyze_rfp(rfp_id):
    """Analyze RFP using AI against company knowledge base"""
    try:
        from app.services.knowledge_base import KnowledgeBaseService
        
        # Get RFP metadata and documents
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get RFP metadata
        cursor.execute("""
            SELECT project_name, organization_group, project_focus, due_date, 
                   country, region, industry, opf_gap_size, opf_gaps, deliverables
            FROM rfp_metadata 
            WHERE id = %s
        """, (rfp_id,))
        rfp_result = cursor.fetchone()
        
        if not rfp_result:
            return jsonify({'error': 'RFP not found'}), 404
        
        # Get all documents for this RFP
        cursor.execute("""
            SELECT document_name, document_text 
            FROM documents 
            WHERE rfp_id = %s 
            ORDER BY created_at DESC
        """, (rfp_id,))
        documents = cursor.fetchall()
        
        if not documents:
            return jsonify({'error': 'No documents found for this RFP. Please upload documents first.'}), 400
        
        cursor.close()
        conn.close()
        
        # Prepare RFP metadata
        rfp_metadata = {
            'project_name': rfp_result[0] or '',
            'organization_group': rfp_result[1] or '',
            'project_focus': rfp_result[2] or '',
            'due_date': rfp_result[3].isoformat() if rfp_result[3] else None,
            'country': rfp_result[4] or '',
            'region': rfp_result[5] or '',
            'industry': rfp_result[6] or '',
            'opf_gap_size': rfp_result[7] or '',
            'opf_gaps': rfp_result[8] or '',
            'deliverables': rfp_result[9] or ''
        }
        
        # Combine all document text
        rfp_text = "\n\n".join([
            f"Document: {doc[0]}\n{doc[1]}" 
            for doc in documents
        ])
        
        # Initialize knowledge base service
        kb_service = KnowledgeBaseService()
        
        # Try to initialize knowledge base if it doesn't exist
        try:
            global _kb_initializing
            
            # Check current status using helper function
            status_result = _check_knowledge_base_status()
            
            if not status_result['success']:
                return jsonify({'error': status_result['error']}), 500
            
            # If not initialized, initialize it
            if status_result['status'] == 'not_initialized':
                # Check if another process is already initializing
                if _kb_initializing:
                    return jsonify({'error': 'Knowledge base is currently being initialized by another process. Please wait a moment and try again.'}), 429
                
                # Set lock and initialize
                _kb_initializing = True
                try:
                    print("Knowledge base not initialized, initializing now...")
                    char_count = kb_service.load_knowledge_base("knowledge_base")
                    print(f"Knowledge base initialization completed with {char_count} characters loaded")
                finally:
                    _kb_initializing = False
            else:
                print(f"Knowledge base already initialized with {status_result['char_count']} characters, proceeding with analysis")
        except Exception as e:
            print(f"Error during knowledge base initialization: {e}")
            # Ensure lock is released on error
            _kb_initializing = False
            return jsonify({'error': f'Failed to initialize knowledge base: {str(e)}'}), 500
        
        # Perform AI analysis
        analysis = kb_service.analyze_rfp(rfp_text, rfp_metadata)
        
        # Debug: Print analysis structure
        print(f"Analysis structure: {type(analysis)}")
        print(f"Analysis keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'Not a dict'}")
        
        # Ensure analysis is a dictionary
        if not isinstance(analysis, dict):
            analysis = {'error': 'Analysis result is not a dictionary'}
        
        # Save analysis results to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get extracted metadata if available
        extracted_metadata = analysis.get('extracted_metadata', {})
        
        # Debug: Print extracted metadata structure
        print(f"Extracted metadata: {extracted_metadata}")
        print(f"Extracted metadata type: {type(extracted_metadata)}")
        
        # Helper function to safely extract string values
        def safe_get_string(data, key, default=''):
            value = data.get(key, default)
            print(f"Processing key '{key}' with value: {value} (type: {type(value)})")
            if isinstance(value, dict):
                return str(value)  # Convert dict to string
            elif isinstance(value, list):
                return str(value)  # Convert list to string
            elif value is None:
                return default
            else:
                return str(value)  # Convert any other type to string
        
        # Update both AI analysis results and extracted metadata
        cursor.execute("""
            UPDATE rfp_metadata 
            SET 
                ai_fit_assessment = %s,
                ai_competitive_position = %s,
                ai_key_strengths = %s,
                ai_gaps_challenges = %s,
                ai_resource_requirements = %s,
                ai_risk_assessment = %s,
                ai_recommendations = %s,
                ai_analysis_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            safe_get_string(analysis, 'fit_assessment', ''),
            safe_get_string(analysis, 'competitive_position', ''),
            safe_get_string(analysis, 'key_strengths', ''),
            safe_get_string(analysis, 'gaps_challenges', ''),
            safe_get_string(analysis, 'resource_requirements', ''),
            safe_get_string(analysis, 'risk_assessment', ''),
            safe_get_string(analysis, 'recommendations', ''),
            rfp_id
        ))
        
        # Update metadata fields individually to avoid type conflicts
        try:
            if extracted_metadata.get('organization_group'):
                cursor.execute("UPDATE rfp_metadata SET organization_group = %s WHERE id = %s", 
                             (str(extracted_metadata['organization_group']), rfp_id))
            
            if extracted_metadata.get('country'):
                cursor.execute("UPDATE rfp_metadata SET country = %s WHERE id = %s", 
                             (str(extracted_metadata['country']), rfp_id))
            
            if extracted_metadata.get('region'):
                cursor.execute("UPDATE rfp_metadata SET region = %s WHERE id = %s", 
                             (str(extracted_metadata['region']), rfp_id))
            
            if extracted_metadata.get('industry'):
                cursor.execute("UPDATE rfp_metadata SET industry = %s WHERE id = %s", 
                             (str(extracted_metadata['industry']), rfp_id))
            
            if extracted_metadata.get('project_focus'):
                cursor.execute("UPDATE rfp_metadata SET project_focus = %s WHERE id = %s", 
                             (str(extracted_metadata['project_focus']), rfp_id))
            
            if extracted_metadata.get('opf_gap_size'):
                cursor.execute("UPDATE rfp_metadata SET opf_gap_size = %s WHERE id = %s", 
                             (str(extracted_metadata['opf_gap_size']), rfp_id))
            
            if extracted_metadata.get('opf_gaps'):
                cursor.execute("UPDATE rfp_metadata SET opf_gaps = %s WHERE id = %s", 
                             (str(extracted_metadata['opf_gaps']), rfp_id))
            
            if extracted_metadata.get('deliverables'):
                cursor.execute("UPDATE rfp_metadata SET deliverables = %s WHERE id = %s", 
                             (str(extracted_metadata['deliverables']), rfp_id))
            
            if extracted_metadata.get('posting_contact'):
                cursor.execute("UPDATE rfp_metadata SET posting_contact = %s WHERE id = %s", 
                             (str(extracted_metadata['posting_contact']), rfp_id))
            
            if extracted_metadata.get('potential_experts'):
                cursor.execute("UPDATE rfp_metadata SET potential_experts = %s WHERE id = %s", 
                             (str(extracted_metadata['potential_experts']), rfp_id))
            
            if extracted_metadata.get('project_cost'):
                # Validate and format the project cost
                project_cost = extracted_metadata['project_cost']
                try:
                    # Try to convert to float and ensure it's a valid number
                    if project_cost and project_cost != 'null':
                        cost_value = float(project_cost)
                        if cost_value > 0:  # Only accept positive costs
                            cursor.execute("UPDATE rfp_metadata SET project_cost = %s WHERE id = %s", 
                                         (cost_value, rfp_id))
                except (ValueError, TypeError) as e:
                    print(f"Invalid project cost '{project_cost}': {e}")
                    # Skip updating this field if cost is invalid
            
            if extracted_metadata.get('currency'):
                cursor.execute("UPDATE rfp_metadata SET currency = %s WHERE id = %s", 
                             (str(extracted_metadata['currency']), rfp_id))
            
            if extracted_metadata.get('specific_staffing_needs'):
                cursor.execute("UPDATE rfp_metadata SET specific_staffing_needs = %s WHERE id = %s", 
                             (str(extracted_metadata['specific_staffing_needs']), rfp_id))
            
            if extracted_metadata.get('due_date'):
                # Validate and format the due date
                due_date = extracted_metadata['due_date']
                try:
                    # Try to parse the date and ensure it's in YYYY-MM-DD format
                    if due_date and due_date != 'null':
                        # If it's just a year, convert to YYYY-01-01
                        if len(due_date) == 4 and due_date.isdigit():
                            due_date = f"{due_date}-01-01"
                        # If it's YYYY-MM, convert to YYYY-MM-01
                        elif len(due_date) == 7 and due_date.count('-') == 1:
                            due_date = f"{due_date}-01"
                        
                        # Validate the final date format
                        from datetime import datetime
                        datetime.strptime(due_date, '%Y-%m-%d')
                        
                        cursor.execute("UPDATE rfp_metadata SET due_date = %s WHERE id = %s", 
                                     (due_date, rfp_id))
                except (ValueError, TypeError) as e:
                    print(f"Invalid date format '{due_date}': {e}")
                    # Skip updating this field if date is invalid
        except Exception as e:
            print(f"Error updating extracted metadata: {e}")
            print(f"Error type: {type(e)}")
            raise  # Re-raise to see the full error
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Try to find relevant members based on the analysis
        member_matching_result = None
        try:
            from app.services.member_matcher import MemberMatcherService
            matcher_service = MemberMatcherService()
            member_matching_result = matcher_service.find_relevant_members(analysis)
        except Exception as member_error:
            print(f"Member matching failed: {member_error}")
            member_matching_result = {
                'success': False,
                'error': f'Member matching failed: {str(member_error)}',
                'keywords': [],
                'members': []
            }
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'rfp_id': rfp_id,
            'documents_analyzed': len(documents),
            'member_matching': member_matching_result
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred during AI analysis: {str(e)}'}), 500


# Global flag to prevent multiple simultaneous initializations
_kb_initializing = False

def _check_knowledge_base_status():
    """Helper function to check knowledge base status consistently"""
    try:
        import os
        from app.services.knowledge_base import KnowledgeBaseService
        
        kb_service = KnowledgeBaseService()
        
        # Check if knowledge base directory exists and has text files
        if not os.path.exists(kb_service.knowledge_base_path):
            return {
                'success': True,
                'status': 'not_initialized',
                'char_count': 0,
                'message': 'Knowledge base directory not found'
            }
        
        # Count text files in knowledge base directory
        txt_files = [f for f in os.listdir(kb_service.knowledge_base_path) if f.endswith('.txt')]
        
        if not txt_files:
            return {
                'success': True,
                'status': 'not_initialized',
                'char_count': 0,
                'message': 'No text files found in knowledge base directory'
            }
        
        # Try to load knowledge base to get character count
        try:
            char_count = kb_service.load_knowledge_base()
            return {
                'success': True,
                'status': 'initialized',
                'char_count': char_count,
                'file_count': len(txt_files),
                'message': f'Knowledge base is initialized with {len(txt_files)} files ({char_count} characters)'
            }
        except Exception as e:
            return {
                'success': True,
                'status': 'not_initialized',
                'char_count': 0,
                'message': f'Knowledge base files found but could not load: {str(e)}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Error checking knowledge base status: {str(e)}'
        }

@bp.route('/api/knowledge-base-status', methods=['GET'])
@login_required
def get_knowledge_base_status():
    """Check the status of the knowledge base"""
    result = _check_knowledge_base_status()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({'error': result['error']}), 500


@bp.route('/api/init-knowledge-base', methods=['POST'])
@login_required
def init_knowledge_base():
    """Manually initialize the knowledge base"""
    try:
        data = request.get_json() or {}
        force_reset = data.get('force_reset', False)
        
        # First check current status
        status_result = _check_knowledge_base_status()
        
        if not status_result['success']:
            return jsonify({'error': status_result['error']}), 500
        
        # If already initialized and not forcing reset, return status
        if status_result['status'] == 'initialized' and not force_reset:
            return jsonify({
                'success': True,
                'already_initialized': True,
                'message': f"Knowledge base is already initialized with {status_result.get('file_count', 0)} files ({status_result['char_count']} characters). Use force_reset=true to reinitialize.",
                'char_count': status_result['char_count'],
                'file_count': status_result.get('file_count', 0)
            })
        
        # Initialize the knowledge base
        from app.services.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        char_count = kb_service.load_knowledge_base("knowledge_base", force_reset=force_reset)
        
        # Count files loaded
        txt_files = [f for f in os.listdir("knowledge_base") if f.endswith('.txt')]
        file_count = len(txt_files)
        
        action = "reinitialized" if force_reset else "initialized"
        return jsonify({
            'success': True,
            'already_initialized': False,
            'message': f'Knowledge base {action} successfully with {file_count} files ({char_count} characters)',
            'char_count': char_count,
            'file_count': file_count,
            'force_reset': force_reset
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to initialize knowledge base: {str(e)}'}), 500


# Tender Scraping Endpoints
@bp.route('/api/tenders/scrape', methods=['POST'])
@login_required
def scrape_tenders():
    """Scrape tenders from all configured sources"""
    try:
        from app.services.tender_scraper import TenderScraper
        import threading
        import time
        
        # Create a simple timeout mechanism
        results = {'error': 'Scraping timed out'}
        scraping_complete = threading.Event()
        
        def scrape_with_timeout():
            nonlocal results
            try:
                scraper = TenderScraper()
                results = scraper.scrape_all_sources()
                
                # Save to database if tenders were found
                if results.get('total_found', 0) > 0:
                    conn = get_database_connection()
                    success = scraper.save_tenders_to_database(
                        results['aus_tenders'] + results['giz_tenders'], 
                        conn
                    )
                    conn.close()
                    
                    if success:
                        results['message'] = f"Successfully scraped and saved {results['total_found']} tenders"
                    else:
                        results['message'] = f"Scraped {results['total_found']} tenders but failed to save to database"
                else:
                    results['message'] = "No climate-related tenders found"
                    
            except Exception as e:
                results = {'error': f'Scraping failed: {str(e)}'}
            finally:
                scraping_complete.set()
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(target=scrape_with_timeout)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        # Wait for completion or timeout (45 seconds)
        if scraping_complete.wait(timeout=45):
            return jsonify(results)
        else:
            return jsonify({'error': 'Scraping operation timed out after 45 seconds'}), 408
            
    except Exception as e:
        return jsonify({'error': f'Failed to scrape tenders: {str(e)}'}), 500


@bp.route('/api/tenders/scrape-aus', methods=['POST'])
@login_required
def scrape_australian_tenders():
    """Scrape tenders from Australian Government source only"""
    try:
        from app.services.tender_scraper import TenderScraper
        import threading
        
        # Create a simple timeout mechanism
        results = {'error': 'Scraping timed out'}
        scraping_complete = threading.Event()
        
        def scrape_with_timeout():
            nonlocal results
            try:
                scraper = TenderScraper()
                aus_tenders = scraper.scrape_aus_tenders()
                
                results = {
                    'aus_tenders': aus_tenders,
                    'total_found': len(aus_tenders),
                    'scraped_at': scraper.scrape_all_sources()['scraped_at']
                }
                
                # Save to database if tenders were found
                if results['total_found'] > 0:
                    conn = get_database_connection()
                    success = scraper.save_tenders_to_database(aus_tenders, conn)
                    conn.close()
                    
                    if success:
                        results['message'] = f"Successfully scraped and saved {results['total_found']} Australian tenders"
                        results['success'] = True
                    else:
                        results['message'] = f"Scraped {results['total_found']} Australian tenders but failed to save to database"
                        results['success'] = False
                else:
                    results['message'] = "No climate-related Australian tenders found"
                    results['success'] = True
                    
            except Exception as e:
                results = {'error': f'Scraping failed: {str(e)}', 'success': False}
            finally:
                scraping_complete.set()
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(target=scrape_with_timeout)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        # Wait for completion or timeout (30 seconds)
        if scraping_complete.wait(timeout=30):
            return jsonify(results)
        else:
            return jsonify({'error': 'Scraping operation timed out after 30 seconds'}), 408
            
    except Exception as e:
        return jsonify({'error': f'Failed to scrape Australian tenders: {str(e)}'}), 500


@bp.route('/api/tenders/scrape-giz', methods=['POST'])
@login_required
def scrape_giz_tenders():
    """Scrape tenders from GIZ source only"""
    try:
        from app.services.tender_scraper import TenderScraper
        import threading
        
        # Create a simple timeout mechanism
        results = {'error': 'Scraping timed out'}
        scraping_complete = threading.Event()
        
        def scrape_with_timeout():
            nonlocal results
            try:
                scraper = TenderScraper()
                giz_tenders = scraper.scrape_giz_tenders()
                
                results = {
                    'giz_tenders': giz_tenders,
                    'total_found': len(giz_tenders),
                    'scraped_at': scraper.scrape_all_sources()['scraped_at']
                }
                
                # Save to database if tenders were found
                if results['total_found'] > 0:
                    conn = get_database_connection()
                    success = scraper.save_tenders_to_database(giz_tenders, conn)
                    conn.close()
                    
                    if success:
                        results['message'] = f"Successfully scraped and saved {results['total_found']} GIZ tenders"
                        results['success'] = True
                    else:
                        results['message'] = f"Scraped {results['total_found']} GIZ tenders but failed to save to database"
                        results['success'] = False
                else:
                    results['message'] = "No climate-related GIZ tenders found"
                    results['success'] = True
                    
            except Exception as e:
                results = {'error': f'Scraping failed: {str(e)}', 'success': False}
            finally:
                scraping_complete.set()
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(target=scrape_with_timeout)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        # Wait for completion or timeout (30 seconds)
        if scraping_complete.wait(timeout=30):
            return jsonify(results)
        else:
            return jsonify({'error': 'Scraping operation timed out after 30 seconds'}), 408
            
    except Exception as e:
        return jsonify({'error': f'Failed to scrape GIZ tenders: {str(e)}'}), 500


@bp.route('/api/tenders/scrape-undp', methods=['POST'])
@login_required
def scrape_undp_tenders():
    """Scrape tenders from UNDP source only"""
    try:
        from app.services.tender_scraper import TenderScraper
        import threading
        
        # Create a simple timeout mechanism
        results = {'error': 'Scraping timed out'}
        scraping_complete = threading.Event()
        
        def scrape_with_timeout():
            nonlocal results
            try:
                scraper = TenderScraper()
                undp_tenders = scraper.scrape_undp_tenders()
                
                results = {
                    'undp_tenders': undp_tenders,
                    'total_found': len(undp_tenders),
                    'scraped_at': scraper.scrape_all_sources()['scraped_at']
                }
                
                # Save to database if tenders were found
                if results['total_found'] > 0:
                    conn = get_database_connection()
                    success = scraper.save_tenders_to_database(undp_tenders, conn)
                    conn.close()
                    
                    if success:
                        results['message'] = f"Successfully scraped and saved {results['total_found']} UNDP tenders"
                        results['success'] = True
                    else:
                        results['message'] = f"Scraped {results['total_found']} UNDP tenders but failed to save to database"
                        results['success'] = False
                else:
                    results['message'] = "No climate-related UNDP tenders found"
                    results['success'] = True
                    
            except Exception as e:
                results = {'error': f'Scraping failed: {str(e)}', 'success': False}
            finally:
                scraping_complete.set()
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(target=scrape_with_timeout)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        # Wait for completion or timeout (30 seconds)
        if scraping_complete.wait(timeout=30):
            return jsonify(results)
        else:
            return jsonify({'error': 'Scraping operation timed out after 30 seconds'}), 408
            
    except Exception as e:
        return jsonify({'error': f'Failed to scrape UNDP tenders: {str(e)}'}), 500


@bp.route('/api/tenders/list', methods=['GET'])
@login_required
def get_tenders_list():
    """Get list of all scraped tenders"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        source = request.args.get('source')
        processed = request.args.get('processed')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = """
            SELECT id, title, description, closing_date, organization, link, source, 
                   scraped_at, is_climate_related, processed, created_at
            FROM scraped_tenders 
            WHERE 1=1
        """
        params = []
        
        if source:
            query += " AND source = %s"
            params.append(source)
            
        if processed is not None:
            query += " AND processed = %s"
            params.append(processed == 'true')
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        tenders = []
        for row in cursor.fetchall():
            tenders.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'closing_date': row[3],
                'organization': row[4],
                'link': row[5],
                'source': row[6],
                'scraped_at': row[7].isoformat() if row[7] else None,
                'is_climate_related': row[8],
                'processed': row[9],
                'created_at': row[10].isoformat() if row[10] else None
            })
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM scraped_tenders WHERE 1=1"
        count_params = []
        
        if source:
            count_query += " AND source = %s"
            count_params.append(source)
            
        if processed is not None:
            count_query += " AND processed = %s"
            count_params.append(processed == 'true')
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'tenders': tenders,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get tenders list: {str(e)}'}), 500


@bp.route('/api/tenders/stats', methods=['GET'])
@login_required
def get_tenders_stats():
    """Get statistics about scraped tenders"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get total counts by source
        cursor.execute("""
            SELECT source, COUNT(*) as count, 
                   COUNT(CASE WHEN processed = true THEN 1 END) as processed_count
            FROM scraped_tenders 
            GROUP BY source
        """)
        
        source_stats = {}
        total_tenders = 0
        total_processed = 0
        
        for row in cursor.fetchall():
            source_stats[row[0]] = {
                'total': row[1],
                'processed': row[2],
                'unprocessed': row[1] - row[2]
            }
            total_tenders += row[1]
            total_processed += row[2]
        
        # Get recent activity
        cursor.execute("""
            SELECT DATE(scraped_at) as date, COUNT(*) as count
            FROM scraped_tenders 
            WHERE scraped_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(scraped_at)
            ORDER BY date DESC
        """)
        
        recent_activity = []
        for row in cursor.fetchall():
            recent_activity.append({
                'date': row[0].isoformat(),
                'count': row[1]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_tenders': total_tenders,
            'total_processed': total_processed,
            'total_unprocessed': total_tenders - total_processed,
            'source_stats': source_stats,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get tenders stats: {str(e)}'}), 500


@bp.route('/api/tenders/mark-processed', methods=['POST'])
@login_required
def mark_tender_processed():
    """Mark a tender as processed"""
    try:
        data = request.get_json()
        tender_id = data.get('tender_id')
        processed = data.get('processed', True)
        
        if not tender_id:
            return jsonify({'error': 'Tender ID is required'}), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scraped_tenders 
            SET processed = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (processed, tender_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Tender not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Tender marked as {"processed" if processed else "unprocessed"}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to mark tender: {str(e)}'}), 500


@bp.route('/api/rfp/<int:rfp_id>/find-members', methods=['POST'])
@login_required
def find_relevant_members(rfp_id):
    """Find relevant members for an RFP based on analysis"""
    try:
        from app.services.member_matcher import MemberMatcherService
        
        # Get RFP analysis from database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ai_fit_assessment, ai_competitive_position, ai_key_strengths, 
                   ai_gaps_challenges, ai_resource_requirements, ai_risk_assessment, 
                   ai_recommendations, project_name
            FROM rfp_metadata 
            WHERE id = %s
        """, (rfp_id,))
        
        rfp_result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not rfp_result:
            return jsonify({'error': 'RFP not found'}), 404
        
        # Check if analysis exists
        if not rfp_result[0]:  # ai_fit_assessment
            return jsonify({'error': 'No AI analysis found for this RFP. Please run the analysis first.'}), 400
        
        # Prepare analysis data
        analysis = {
            'fit_assessment': rfp_result[0] or '',
            'competitive_position': rfp_result[1] or '',
            'key_strengths': rfp_result[2] or '',
            'gaps_challenges': rfp_result[3] or '',
            'resource_requirements': rfp_result[4] or '',
            'risk_assessment': rfp_result[5] or '',
            'recommendations': rfp_result[6] or '',
            'project_name': rfp_result[7] or ''
        }
        
        # Initialize member matcher service
        matcher_service = MemberMatcherService()
        
        # Find relevant members
        result = matcher_service.find_relevant_members(analysis)
        
        # Add RFP context to the result
        result['rfp_id'] = rfp_id
        result['project_name'] = analysis['project_name']
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error finding relevant members: {str(e)}'}), 500

