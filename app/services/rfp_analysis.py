import os
import re
import tempfile
from app.services.database import search_database
from app.utils.file_utils import extract_text_from_pdf, extract_text_from_docx

def extract_keywords_from_text(text):
    """Extract key requirements and keywords from text"""
    # Common RFP keywords and requirements
    keywords = []
    
    # Look for specific patterns
    patterns = [
        r'required.*?experience',
        r'must.*?have',
        r'minimum.*?years',
        r'qualifications.*?include',
        r'experience.*?with',
        r'knowledge.*?of',
        r'proficiency.*?in',
        r'expertise.*?in',
        r'familiarity.*?with',
        r'understanding.*?of'
    ]
    
    # Extract sentences containing these patterns
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Only consider substantial sentences
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    keywords.append(sentence)
                    break
    
    return keywords

def find_matching_experts(keywords):
    """Find experts matching the extracted keywords"""
    if not keywords:
        return []
    
    # Combine all keywords into a search string
    search_terms = ', '.join(keywords)
    
    # Search the database
    results = search_database(search_terms)
    
    # Return top matches (limit to 10)
    return results[:10]

def analyze_rfp_document(file, extract_keywords=True, find_experts=True):
    """Analyze RFP document and find matching experts"""
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        file.save(temp_file.name)
        temp_file_path = temp_file.name
    
    try:
        # Extract text based on file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension == '.pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file_extension in ['.doc', '.docx']:
            text = extract_text_from_docx(temp_file_path)
        else:
            return {'error': 'Unsupported file format. Please upload PDF, DOC, or DOCX.'}
        
        if not text:
            return {'error': 'Could not extract text from the uploaded file.'}
        
        result = {
            'filename': file.filename,
            'text_length': len(text),
            'keywords': [],
            'experts': []
        }
        
        # Extract keywords if requested
        if extract_keywords:
            keywords = extract_keywords_from_text(text)
            result['keywords'] = keywords
        
        # Find matching experts if requested
        if find_experts:
            experts = find_matching_experts(keywords if extract_keywords else [])
            result['experts'] = experts
        
        return result
        
    except Exception as e:
        return {'error': f'Error processing file: {str(e)}'}
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
