import os
import psycopg2
from urllib.parse import urlparse

def get_database_connection():
    """Get database connection based on environment"""
    database_url = os.environ.get('DATABASE_URL')
    
    # For local development, connect to local database if DATABASE_URL is not set
    if not database_url:
        # Local development connection
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='opf_community_local',
            user='thomaswalter',
            password=''  # No password for local development
        )
        return conn
    
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Connect to PostgreSQL
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    
    return conn

def search_database(keywords, source_filters=None, experience_filters=None, sustainability_experience_filters=None, competencies_filters=None, sectors_filters=None):
    """Search for multiple keywords across all columns in the final table using AND logic"""
    conn = get_database_connection()
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
    
    cursor.close()
    conn.close()
    return formatted_results

def get_stats():
    """Get basic statistics about the database"""
    conn = get_database_connection()
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
    
    cursor.close()
    conn.close()
    
    return {
        'total_records': total_records,
        'records_with_linkedins': records_with_linkedins,
        'records_with_resumes': records_with_resumes
    }

def get_user_by_email(email):
    """Get a single user by email address"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM final WHERE email = %s", (email,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return None
        
    finally:
        cursor.close()
        conn.close()
