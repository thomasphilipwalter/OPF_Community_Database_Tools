from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_session import Session
import os
import requests
import re
from auth import get_user_by_email, validate_email
from datetime import datetime
from config import config
from google_auth import verify_google_token, create_user_from_google_info

app = Flask(__name__)

# Configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Initialize extensions
Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID (email)"""
    return get_user_by_email(user_id)

def search_database(keywords, source_filters=None, experience_filters=None, sustainability_experience_filters=None, competencies_filters=None, sectors_filters=None):
    """Search for multiple keywords across all columns in the final table using AND logic"""
    # Use environment variable for database URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("DATABASE_URL environment variable is required")
    
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Connect to PostgreSQL
    import psycopg2
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    cursor = conn.cursor()
    
    # Get all column names from the final table
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'final' 
        ORDER BY ordinal_position
    """)
    columns = [column[0] for column in cursor.fetchall()]
    
    # Split keywords by comma and clean them
    keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
    
    # Build the search query
    all_conditions = []
    
    # Add keyword conditions if keywords are provided
    if keyword_list:
        for keyword in keyword_list:
            # Build conditions for this keyword across all columns (excluding id)
            keyword_conditions = []
            for column in columns:
                if column != 'id':  # Skip the id column since it's an integer
                    keyword_conditions.append(f"LOWER({column}) LIKE LOWER('%{keyword}%')")
            # Each keyword must be found in at least one column (OR logic within keyword)
            if keyword_conditions:  # Only add condition if there are valid columns
                all_conditions.append(f"({' OR '.join(keyword_conditions)})")
    
    # Add source filtering if specified
    if source_filters and len(source_filters) > 0:
        for source in source_filters:
            # Handle comma-separated values in source column
            all_conditions.append(f"source LIKE '%{source}%'")
    
    # Add experience filtering if specified
    if experience_filters and len(experience_filters) > 0:
        for exp_range in experience_filters:
            all_conditions.append(f"years_xp = '{exp_range}'")
    
    # Add sustainability experience filtering if specified
    if sustainability_experience_filters and len(sustainability_experience_filters) > 0:
        for exp_range in sustainability_experience_filters:
            all_conditions.append(f"years_sustainability_xp = '{exp_range}'")
    
    # Add competencies filtering if specified
    if competencies_filters and len(competencies_filters) > 0:
        for competency in competencies_filters:
            all_conditions.append(f"key_competencies LIKE '%{competency}%'")
    
    # Add sectors filtering if specified
    if sectors_filters and len(sectors_filters) > 0:
        for sector in sectors_filters:
            all_conditions.append(f"key_sectors LIKE '%{sector}%'")
    
    # Build the WHERE clause
    if all_conditions:
        where_clause = f"WHERE {' AND '.join(all_conditions)}"
    else:
        where_clause = ""
    
    query = f"""
    SELECT * FROM final 
    {where_clause}
    ORDER BY first_name, last_name
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Convert results to list of dictionaries with column names
    column_names = [description[0] for description in cursor.description]
    formatted_results = []
    
    for row in results:
        row_dict = {}
        for i, value in enumerate(row):
            row_dict[column_names[i]] = value if value else ""
        formatted_results.append(row_dict)
    
    conn.close()
    return formatted_results

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    """Show login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html', google_client_id=app.config['GOOGLE_CLIENT_ID'])

@app.route('/verify-google-token', methods=['POST'])
def verify_google_token_route():
    """Verify Google ID token from client-side"""
    if current_user.is_authenticated:
        return jsonify({'success': True, 'redirect_url': url_for('index')})
    
    try:
        data = request.get_json()
        credential = data.get('credential')
        
        if not credential:
            return jsonify({'success': False, 'error': 'No credential provided'})
        
        # Verify the token
        user_info, error = verify_google_token(credential)
        if error:
            return jsonify({'success': False, 'error': error})
        
        # Create user and log in
        user = create_user_from_google_info(user_info)
        login_user(user, remember=True)
        
        # Return success response
        next_page = request.args.get('next')
        redirect_url = next_page or url_for('index')
        return jsonify({'success': True, 'redirect_url': redirect_url})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
@login_required
def logout():
    """Handle logout requests"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/search', methods=['POST'])
@login_required
def search():
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

@app.route('/api/stats')
@login_required
def get_stats():
    """Get basic statistics about the database"""
    try:
        # Use environment variable for database URL
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise Exception("DATABASE_URL environment variable is required")
        
        # Handle Railway's postgres:// format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Connect to PostgreSQL
        import psycopg2
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        cursor = conn.cursor()
        
        # Get total number of records
        cursor.execute("SELECT COUNT(*) FROM final")
        total_records = cursor.fetchone()[0]
        
        # Get count of records with LinkedIn profiles
        cursor.execute("SELECT COUNT(*) FROM final WHERE linkedin IS NOT NULL AND linkedin != ''")
        records_with_linkedins = cursor.fetchone()[0]
        
        # Get count of records with resumes
        cursor.execute("SELECT COUNT(*) FROM final WHERE resume IS NOT NULL AND resume != ''")
        records_with_resumes = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_records': total_records,
            'records_with_linkedins': records_with_linkedins,
            'records_with_resumes': records_with_resumes
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

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
                    # Extract key terms from the sentence
                    words = re.findall(r'\b[A-Za-z]{4,}\b', sentence)
                    keywords.extend(words[:5])  # Take first 5 words
                    break
    
    # Remove duplicates and common words
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'so', 'than', 'too', 'very', 'just', 'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'such', 'that', 'theirs', 'them', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'within', 'without', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'}
    
    keywords = [word.lower() for word in keywords if word.lower() not in common_words]
    keywords = list(set(keywords))  # Remove duplicates
    
    return keywords[:20]  # Return top 20 keywords

def find_matching_experts(keywords):
    """Find experts matching the extracted keywords"""
    if not keywords:
        return []
    
    # Connect to database
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
            raise Exception("DATABASE_URL environment variable is required")
        
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    # Connect to PostgreSQL
    import psycopg2
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    
    cursor = conn.cursor()
    
    # Build search query for experts
    keyword_conditions = []
    for keyword in keywords[:10]:  # Use top 10 keywords
        keyword_conditions.append(f"LOWER(current_job) LIKE LOWER('%{keyword}%')")
        keyword_conditions.append(f"LOWER(key_competencies) LIKE LOWER('%{keyword}%')")
        keyword_conditions.append(f"LOWER(linkedin_skills) LIKE LOWER('%{keyword}%')")
        keyword_conditions.append(f"LOWER(current_company) LIKE LOWER('%{keyword}%')")
    
    if keyword_conditions:
        where_clause = f"WHERE {' OR '.join(keyword_conditions)}"
    else:
        where_clause = ""
    
    query = f"""
    SELECT first_name, last_name, current_job, current_company, key_competencies, linkedin_skills
    FROM final 
    {where_clause}
    ORDER BY first_name, last_name
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Format results
    experts = []
    for row in results:
        expert = {
            'first_name': row[0] or '',
            'last_name': row[1] or '',
            'current_job': row[2] or '',
            'current_company': row[3] or '',
            'matched_skills': []
        }
        
        # Find which skills matched
        skills_text = f"{row[4] or ''} {row[5] or ''}"
        for keyword in keywords[:5]:  # Check top 5 keywords
            if keyword.lower() in skills_text.lower():
                expert['matched_skills'].append(keyword)
        
        experts.append(expert)
    
    conn.close()
    return experts

@app.route('/analyze-rfp', methods=['POST'])
@login_required
def analyze_rfp():
    """Analyze uploaded RFP document"""
    try:
        if 'rfp_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['rfp_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        allowed_extensions = {'.pdf', '.doc', '.docx'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload PDF, DOC, or DOCX files.'})
        
        # Save file temporarily
        temp_path = os.path.join('/tmp', f'rfp_{datetime.now().strftime("%Y%m%d_%H%M%S")}{file_ext}')
        file.save(temp_path)
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = extract_text_from_pdf(temp_path)
        elif file_ext in ['.doc', '.docx']:
            text = extract_text_from_docx(temp_path)
        else:
            text = ""
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not text:
            return jsonify({'success': False, 'error': 'Could not extract text from the document'})
        
        # Extract keywords
        keywords = extract_keywords_from_text(text)
        
        # Find matching experts
        experts = find_matching_experts(keywords)
        
        return jsonify({
            'success': True,
            'keywords': keywords,
            'experts': experts
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use environment variables for production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 