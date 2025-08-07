#!/usr/bin/env python3
"""
Database synchronization script for OPF Community Database
Sync data between local PostgreSQL and Railway PostgreSQL
"""

import psycopg2
import csv
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

def get_railway_connection():
    """Get Railway PostgreSQL connection from environment or user input"""
    
    # Try to get from environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("DATABASE_URL not found in environment variables.")
        print("Please enter your Railway PostgreSQL connection string:")
        print("(You can find this in Railway dashboard → PostgreSQL → Connect → Connect with external tool)")
        database_url = input("Database URL: ").strip()
    
    if not database_url:
        print("Error: No database URL provided!")
        return None
    
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url

def get_local_connection():
    """Get local PostgreSQL connection"""
    
    # Try to get from .env.local file
    local_db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'opf_community_local',
        'user': 'postgres',
        'password': ''
    }
    
    # You can modify these parameters based on your local setup
    return local_db_config

def export_to_csv(connection_params, output_file):
    """Export data from PostgreSQL to CSV"""
    
    if isinstance(connection_params, str):
        # Railway connection (URL)
        parsed = urlparse(connection_params)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
    else:
        # Local connection (dict)
        conn = psycopg2.connect(**connection_params)
    
    cursor = conn.cursor()
    
    # Export data
    cursor.execute("SELECT * FROM final")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'final' 
        ORDER BY ordinal_position
    """)
    columns = [column[0] for column in cursor.fetchall()]
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        writer.writerows(rows)
    
    cursor.close()
    conn.close()
    
    print(f"Exported {len(rows)} rows to {output_file}")
    return len(rows)

def import_from_csv(connection_params, csv_file):
    """Import data from CSV to PostgreSQL"""
    
    if isinstance(connection_params, str):
        # Railway connection (URL)
        parsed = urlparse(connection_params)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
    else:
        # Local connection (dict)
        conn = psycopg2.connect(**connection_params)
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM final")
    print("Cleared existing data")
    
    # Read CSV and import
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header row
        
        # Prepare insert statement
        columns = ', '.join(headers)
        placeholders = ', '.join(['%s'] * len(headers))
        insert_query = f"INSERT INTO final ({columns}) VALUES ({placeholders})"
        
        # Insert data
        row_count = 0
        for row in csv_reader:
            cursor.execute(insert_query, row)
            row_count += 1
            
            if row_count % 100 == 0:
                conn.commit()
                print(f"Imported {row_count} rows...")
        
        conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f"Successfully imported {row_count} rows from {csv_file}")

def sync_railway_to_local():
    """Sync Railway database to local database"""
    
    print("Syncing Railway → Local PostgreSQL")
    print("-" * 40)
    
    # Get connections
    railway_url = get_railway_connection()
    if not railway_url:
        return
    
    local_config = get_local_connection()
    
    # Export from Railway
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"railway_export_{timestamp}.csv"
    
    print("Exporting from Railway...")
    export_to_csv(railway_url, csv_file)
    
    # Import to local
    print("Importing to local PostgreSQL...")
    import_from_csv(local_config, csv_file)
    
    # Clean up
    os.remove(csv_file)
    print(f"Removed temporary file: {csv_file}")
    
    print("✅ Sync complete: Railway → Local")

def sync_local_to_railway():
    """Sync local database to Railway database"""
    
    print("Syncing Local PostgreSQL → Railway")
    print("-" * 40)
    
    # Get connections
    railway_url = get_railway_connection()
    if not railway_url:
        return
    
    local_config = get_local_connection()
    
    # Export from local
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"local_export_{timestamp}.csv"
    
    print("Exporting from local PostgreSQL...")
    export_to_csv(local_config, csv_file)
    
    # Import to Railway
    print("Importing to Railway PostgreSQL...")
    import_from_csv(railway_url, csv_file)
    
    # Clean up
    os.remove(csv_file)
    print(f"Removed temporary file: {csv_file}")
    
    print("✅ Sync complete: Local → Railway")

def compare_databases():
    """Compare row counts between local and Railway databases"""
    
    print("Comparing Local vs Railway databases")
    print("-" * 40)
    
    railway_url = get_railway_connection()
    if not railway_url:
        return
    
    local_config = get_local_connection()
    
    # Get Railway count
    parsed = urlparse(railway_url)
    railway_conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    railway_cursor = railway_conn.cursor()
    railway_cursor.execute("SELECT COUNT(*) FROM final")
    railway_count = railway_cursor.fetchone()[0]
    railway_cursor.close()
    railway_conn.close()
    
    # Get local count
    local_conn = psycopg2.connect(**local_config)
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT COUNT(*) FROM final")
    local_count = local_cursor.fetchone()[0]
    local_cursor.close()
    local_conn.close()
    
    print(f"Railway database: {railway_count} rows")
    print(f"Local database:  {local_count} rows")
    
    if railway_count == local_count:
        print("✅ Databases are in sync!")
    else:
        print("⚠️  Databases are out of sync")
        print(f"Difference: {abs(railway_count - local_count)} rows")

def main():
    """Main function"""
    
    print("OPF Community Database - Sync Tool")
    print("=" * 40)
    print("1. Sync Railway → Local")
    print("2. Sync Local → Railway")
    print("3. Compare databases")
    print("4. Exit")
    
    choice = input("\nSelect an option (1-4): ").strip()
    
    if choice == '1':
        sync_railway_to_local()
    elif choice == '2':
        sync_local_to_railway()
    elif choice == '3':
        compare_databases()
    elif choice == '4':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()
