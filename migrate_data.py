#!/usr/bin/env python3
"""
Data migration script to move data from SQLite to PostgreSQL
Run this script locally to export data, then import to Railway PostgreSQL
"""

import sqlite3
import csv
import os
from datetime import datetime

def export_sqlite_data():
    """Export all data from SQLite database to CSV files"""
    
    # Connect to SQLite database
    conn = sqlite3.connect('opf_community.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables: {[table[0] for table in tables]}")
    
    # Export each table
    for table in tables:
        table_name = table[0]
        print(f"Exporting table: {table_name}")
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get all data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Write to CSV
        csv_filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            writer.writerows(rows)
        
        print(f"  Exported {len(rows)} rows to {csv_filename}")
    
    conn.close()
    print("\nExport completed! CSV files created in current directory.")

def create_postgresql_schema():
    """Generate PostgreSQL schema creation script"""
    
    schema_sql = """
-- PostgreSQL Schema for OPF Community Database
-- Run this in your Railway PostgreSQL database

-- Create the final table (main table)
CREATE TABLE IF NOT EXISTS final (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    email_other VARCHAR(255),
    linkedin VARCHAR(500),
    city VARCHAR(255),
    country VARCHAR(255),
    current_job VARCHAR(500),
    current_company VARCHAR(500),
    linkedin_summary TEXT,
    resume TEXT,
    executive_summary TEXT,
    years_xp VARCHAR(50),
    years_sustainability_xp VARCHAR(50),
    linkedin_skills TEXT,
    key_competencies TEXT,
    key_sectors TEXT,
    gender_identity VARCHAR(100),
    race_ethnicity VARCHAR(100),
    lgbtqia VARCHAR(10),
    source VARCHAR(255)
);

-- Create index for better search performance
CREATE INDEX IF NOT EXISTS idx_final_search ON final USING gin(to_tsvector('english', 
    COALESCE(first_name, '') || ' ' || 
    COALESCE(last_name, '') || ' ' || 
    COALESCE(email, '') || ' ' || 
    COALESCE(current_job, '') || ' ' || 
    COALESCE(current_company, '') || ' ' || 
    COALESCE(linkedin_summary, '') || ' ' || 
    COALESCE(executive_summary, '') || ' ' || 
    COALESCE(linkedin_skills, '') || ' ' || 
    COALESCE(key_competencies, '') || ' ' || 
    COALESCE(key_sectors, '')
));
"""
    
    with open('postgresql_schema.sql', 'w') as f:
        f.write(schema_sql)
    
    print("PostgreSQL schema file created: postgresql_schema.sql")

if __name__ == "__main__":
    print("OPF Community Database Migration Tool")
    print("=" * 40)
    
    # Check if SQLite database exists
    if not os.path.exists('opf_community.db'):
        print("Error: opf_community.db not found in current directory")
        exit(1)
    
    # Export data
    export_sqlite_data()
    
    # Create schema
    create_postgresql_schema()
    
    print("\nNext steps:")
    print("1. Go to Railway dashboard")
    print("2. Add a PostgreSQL database to your project")
    print("3. Run the postgresql_schema.sql file in your PostgreSQL database")
    print("4. Import the CSV files into your PostgreSQL database")
    print("5. Set the DATABASE_URL environment variable in Railway") 