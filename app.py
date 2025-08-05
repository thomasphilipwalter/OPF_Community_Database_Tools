from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

def search_database(keywords):
    """Search for multiple keywords across all columns in the final table using AND logic"""
    conn = sqlite3.connect('opfa_community.db')
    cursor = conn.cursor()
    
    # Get all column names from the final table
    cursor.execute("PRAGMA table_info(final)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Split keywords by comma and clean them
    keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
    
    if not keyword_list:
        return []
    
    # Build the search query for each keyword
    all_conditions = []
    
    for keyword in keyword_list:
        # Build conditions for this keyword across all columns
        keyword_conditions = []
        for column in columns:
            keyword_conditions.append(f"LOWER({column}) LIKE LOWER('%{keyword}%')")
        # Each keyword must be found in at least one column (OR logic within keyword)
        all_conditions.append(f"({' OR '.join(keyword_conditions)})")
    
    # All keywords must be found (AND logic between keywords)
    query = f"""
    SELECT * FROM final 
    WHERE {' AND '.join(all_conditions)}
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
        
        if not keywords:
            return jsonify({'error': 'Please enter a keyword or phrase to search for'})
        
        results = search_database(keywords)
        
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
        conn = sqlite3.connect('opfa_community.db')
        cursor = conn.cursor()
        
        # Get total number of records
        cursor.execute("SELECT COUNT(*) FROM final")
        total_records = cursor.fetchone()[0]
        
        # Get count of records with non-null values in key fields
        cursor.execute("SELECT COUNT(*) FROM final WHERE first_name IS NOT NULL AND first_name != ''")
        records_with_names = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM final WHERE current_company IS NOT NULL AND current_company != ''")
        records_with_companies = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_records': total_records,
            'records_with_names': records_with_names,
            'records_with_companies': records_with_companies
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    # Use environment variables for production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 