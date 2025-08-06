#!/usr/bin/env python3
"""
Import CSV data into Railway PostgreSQL database
"""

import psycopg2
import csv
import os
from urllib.parse import urlparse

def import_csv_to_postgres(csv_file, database_url):
    """Import CSV data into PostgreSQL database"""
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    
    cursor = conn.cursor()
    
    # Read CSV file
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
            
            # Commit every 100 rows
            if row_count % 100 == 0:
                conn.commit()
                print(f"Imported {row_count} rows...")
        
        # Final commit
        conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f"Successfully imported {row_count} rows into the final table!")

if __name__ == "__main__":
    csv_file = "final_export_20250806_110630.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        exit(1)
    
    # Get database URL from user
    print("Please enter your Railway PostgreSQL connection string:")
    print("(You can find this in Railway dashboard → PostgreSQL → Connect → Connect with external tool)")
    database_url = input("Database URL: ").strip()
    
    if not database_url:
        print("Error: No database URL provided!")
        exit(1)
    
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"Importing data from {csv_file}...")
    import_csv_to_postgres(csv_file, database_url) 