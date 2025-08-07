#!/usr/bin/env python3
"""
Migrate data from local PostgreSQL to Railway PostgreSQL
This script syncs changes from your local database to the Railway production database
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
    
    # Get local connection from environment
    local_db_url = os.environ.get('DATABASE_URL')
    
    if not local_db_url:
        print("Error: Local DATABASE_URL not found in environment variables")
        print("Make sure your .env file has the local PostgreSQL connection string")
        return None
    
    # Handle Railway's postgres:// format
    if local_db_url.startswith('postgres://'):
        local_db_url = local_db_url.replace('postgres://', 'postgresql://', 1)
    
    return local_db_url

def export_table_to_csv(connection_params, table_name, output_file):
    """Export a table from PostgreSQL to CSV"""
    
    if isinstance(connection_params, str):
        # Parse connection URL
        parsed = urlparse(connection_params)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
    else:
        # Direct connection parameters
        conn = psycopg2.connect(**connection_params)
    
    cursor = conn.cursor()
    
    # Export data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
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
    
    print(f"Exported {len(rows)} rows from {table_name} to {output_file}")
    return len(rows)

def import_csv_to_table(connection_params, csv_file, table_name):
    """Import CSV data into PostgreSQL table"""
    
    if isinstance(connection_params, str):
        # Parse connection URL
        parsed = urlparse(connection_params)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
    else:
        # Direct connection parameters
        conn = psycopg2.connect(**connection_params)
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute(f"DELETE FROM {table_name}")
    print(f"Cleared existing data from {table_name}")
    
    # Read CSV and import
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header row
        
        # Prepare insert statement
        columns = ', '.join([f'"{col}"' for col in headers])
        placeholders = ', '.join(['%s'] * len(headers))
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        # Insert data
        row_count = 0
        for row in csv_reader:
            # Process row data - convert empty strings to None
            processed_row = []
            for value in row:
                if value == '' or value is None:
                    processed_row.append(None)
                else:
                    processed_row.append(value)
            
            cursor.execute(insert_query, processed_row)
            row_count += 1
            
            if row_count % 100 == 0:
                conn.commit()
                print(f"Imported {row_count} rows...")
        
        conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f"Successfully imported {row_count} rows from {csv_file} into {table_name}")

def sync_local_to_railway():
    """Sync local PostgreSQL database to Railway PostgreSQL"""
    
    print("Syncing Local PostgreSQL → Railway PostgreSQL")
    print("=" * 50)
    
    # Get connections
    local_url = get_local_connection()
    if not local_url:
        return False
    
    railway_url = get_railway_connection()
    if not railway_url:
        return False
    
    # Get table names from local database
    parsed = urlparse(local_url)
    local_conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    local_cursor = local_conn.cursor()
    
    # Get all table names
    local_cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    """)
    tables = [table[0] for table in local_cursor.fetchall()]
    local_cursor.close()
    local_conn.close()
    
    print(f"Found {len(tables)} tables in local database: {tables}")
    
    # Sync each table
    total_records = 0
    for table_name in tables:
        print(f"\nSyncing table: {table_name}")
        
        # Create temporary CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f"temp_{table_name}_{timestamp}.csv"
        
        try:
            # Export from local
            print(f"  Exporting from local {table_name}...")
            export_table_to_csv(local_url, table_name, csv_file)
            
            # Import to Railway
            print(f"  Importing to Railway {table_name}...")
            import_csv_to_table(railway_url, csv_file, table_name)
            
            # Clean up temporary file
            os.remove(csv_file)
            print(f"  ✅ Synced {table_name}")
            
        except Exception as e:
            print(f"  ❌ Error syncing {table_name}: {e}")
            if os.path.exists(csv_file):
                os.remove(csv_file)
            continue
    
    print(f"\n✅ Sync completed!")
    return True

def preview_sync():
    """Preview what would be synced"""
    
    print("Preview: Local vs Railway Database")
    print("=" * 40)
    
    # Get connections
    local_url = get_local_connection()
    if not local_url:
        return False
    
    railway_url = get_railway_connection()
    if not railway_url:
        return False
    
    # Compare record counts
    tables_to_check = ['final']  # Main table
    
    for table_name in tables_to_check:
        print(f"\nTable: {table_name}")
        
        # Get local count
        parsed = urlparse(local_url)
        local_conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        local_cursor = local_conn.cursor()
        local_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        local_count = local_cursor.fetchone()[0]
        local_cursor.close()
        local_conn.close()
        
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
        railway_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        railway_count = railway_cursor.fetchone()[0]
        railway_cursor.close()
        railway_conn.close()
        
        print(f"  Local:  {local_count} records")
        print(f"  Railway: {railway_count} records")
        
        if local_count == railway_count:
            print("  ✅ Databases are in sync")
        else:
            print(f"  ⚠️  Difference: {abs(local_count - railway_count)} records")

def main():
    """Main function"""
    
    print("Local to Railway Database Migration Tool")
    print("=" * 50)
    print("This tool syncs your local PostgreSQL database to Railway")
    print()
    print("1. Preview sync (compare local vs Railway)")
    print("2. Sync local → Railway (overwrites Railway data)")
    print("3. Exit")
    
    choice = input("\nSelect an option (1-3): ").strip()
    
    if choice == '1':
        preview_sync()
    elif choice == '2':
        # Confirm before proceeding
        confirm = input("\n⚠️  This will OVERWRITE Railway data with local data. Continue? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            sync_local_to_railway()
        else:
            print("Sync cancelled.")
    elif choice == '3':
        print("Goodbye!")
        return
    else:
        print("Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main()
