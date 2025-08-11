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
                    doc_count = kb_service.process_knowledge_base("knowledge_base")
                    print(f"Knowledge base initialization completed with {doc_count} document chunks")
                finally:
                    _kb_initializing = False
            else:
                print(f"Knowledge base already initialized with {status_result['document_count']} document chunks, proceeding with analysis")
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
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'rfp_id': rfp_id,
            'documents_analyzed': len(documents)
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
        from langchain_chroma import Chroma
        
        kb_service = KnowledgeBaseService()
        
        # Try to load existing vector store if it exists on disk
        if not kb_service.vector_store:
            try:
                # Check if the chroma_db directory exists and has content
                if os.path.exists(kb_service.chroma_db_path):
                    # Try to load the existing vector store
                    kb_service.vector_store = Chroma(
                        persist_directory=kb_service.chroma_db_path,
                        embedding_function=kb_service.embeddings
                    )
            except Exception as e:
                print(f"Could not load existing vector store: {e}")
                pass
        
        # Check if knowledge base exists and has documents
        if kb_service.vector_store and kb_service.vector_store._collection.count() > 0:
            doc_count = kb_service.vector_store._collection.count()
            return {
                'success': True,
                'status': 'initialized',
                'document_count': doc_count,
                'message': f'Knowledge base is initialized with {doc_count} document chunks'
            }
        else:
            return {
                'success': True,
                'status': 'not_initialized',
                'document_count': 0,
                'message': 'Knowledge base is not initialized'
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
        # First check current status
        status_result = _check_knowledge_base_status()
        
        if not status_result['success']:
            return jsonify({'error': status_result['error']}), 500
        
        # If already initialized, return status
        if status_result['status'] == 'initialized':
            return jsonify({
                'success': True,
                'already_initialized': True,
                'message': f"Knowledge base is already initialized with {status_result['document_count']} document chunks. No action needed.",
                'document_count': status_result['document_count']
            })
        
        # Initialize the knowledge base
        from app.services.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        doc_count = kb_service.process_knowledge_base("knowledge_base")
        
        return jsonify({
            'success': True,
            'already_initialized': False,
            'message': f'Knowledge base initialized successfully with {doc_count} document chunks',
            'document_count': doc_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to initialize knowledge base: {str(e)}'}), 500

