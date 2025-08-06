from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

def search_database(keywords, source_filters=None, experience_filters=None, sustainability_experience_filters=None):
    """Search for multiple keywords across all columns in the final table using AND logic"""
    conn = sqlite3.connect('opf_community.db')
    cursor = conn.cursor()
    
    # Get all column names from the final table
    cursor.execute("PRAGMA table_info(final)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Split keywords by comma and clean them
    keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
    
    # Build the search query
    all_conditions = []
    
    # Add keyword conditions if keywords are provided
    if keyword_list:
        for keyword in keyword_list:
            # Build conditions for this keyword across all columns
            keyword_conditions = []
            for column in columns:
                keyword_conditions.append(f"LOWER({column}) LIKE LOWER('%{keyword}%')")
            # Each keyword must be found in at least one column (OR logic within keyword)
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
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        keywords = data.get('keyword', '').strip()
        source_filters = data.get('source_filters', [])
        experience_filters = data.get('experience_filters', [])
        sustainability_experience_filters = data.get('sustainability_experience_filters', [])
        
        results = search_database(keywords, source_filters, experience_filters, sustainability_experience_filters)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'keyword': keywords
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

@app.route('/api/stats')
def get_stats():
    """Get basic statistics about the database"""
    try:
        conn = sqlite3.connect('opf_community.db')
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



if __name__ == '__main__':
    # Use environment variables for production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 