#!/usr/bin/env python3
"""
Setup script to create a local PostgreSQL database that mirrors the Railway setup
This allows you to work with the same database type locally and in production
"""

import psycopg2
import sqlite3
import csv
import os
from urllib.parse import urlparse
from datetime import datetime

def create_local_postgresql_database():
    """Create a local PostgreSQL database and migrate data from SQLite"""
    
    # Local PostgreSQL connection parameters
    # You can modify these based on your local PostgreSQL setup
    local_db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'opf_community_local',
        'user': 'postgres',  # Change to your PostgreSQL username
        'password': ''  # Add your password if needed
    }
    
    print("Setting up local PostgreSQL database...")
    
    # First, connect to PostgreSQL server (without specifying database)
    conn_params = local_db_config.copy()
    conn_params['database'] = 'postgres'  # Connect to default database
    
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create the database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{local_db_config['database']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {local_db_config['database']}")
            print(f"Created database: {local_db_config['database']}")
        else:
            print(f"Database {local_db_config['database']} already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is installed and running locally")
        print("You may need to modify the connection parameters in this script")
        return False
    
    # Now connect to the new database and create schema
    conn_params['database'] = local_db_config['database']
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Create the schema
    schema_sql = """
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
    
    cursor.execute(schema_sql)
    conn.commit()
    print("Created database schema")
    
    # Migrate data from SQLite if it exists
    if os.path.exists('opf_community.db'):
        print("Migrating data from SQLite to PostgreSQL...")
        migrate_sqlite_to_postgresql(cursor, conn)
    
    cursor.close()
    conn.close()
    
    # Create .env file for local development
    create_local_env_file(local_db_config)
    
    print("\n✅ Local PostgreSQL setup complete!")
    print(f"Database: {local_db_config['database']}")
    print("You can now use the same database type locally and in production")
    
    return True

def migrate_sqlite_to_postgresql(cursor, conn):
    """Migrate data from SQLite to PostgreSQL"""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('opf_community.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get all data from SQLite
    sqlite_cursor.execute("SELECT * FROM final")
    rows = sqlite_cursor.fetchall()
    
    # Get column names
    sqlite_cursor.execute("PRAGMA table_info(final)")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    # Insert data into PostgreSQL
    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    insert_query = f"INSERT INTO final ({columns_str}) VALUES ({placeholders})"
    
    row_count = 0
    for row in rows:
        cursor.execute(insert_query, row)
        row_count += 1
        
        if row_count % 100 == 0:
            conn.commit()
            print(f"  Migrated {row_count} rows...")
    
    conn.commit()
    sqlite_conn.close()
    
    print(f"  Successfully migrated {row_count} rows from SQLite to PostgreSQL")

def create_local_env_file(db_config):
    """Create a local .env file for development"""
    
    env_content = f"""# Local Development Environment Variables
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
GOOGLE_CLIENT_ID=your-google-client-id-here

# Local PostgreSQL Database
DATABASE_URL=postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}
"""
    
    with open('.env.local', 'w') as f:
        f.write(env_content)
    
    print("Created .env.local file for local development")

def sync_with_railway():
    """Sync local PostgreSQL with Railway PostgreSQL"""
    
    print("\nTo sync your local PostgreSQL with Railway:")
    print("1. Export data from Railway PostgreSQL")
    print("2. Import into your local PostgreSQL")
    print("3. Or use the reverse process to push local changes to Railway")
    print("\nYou can use the existing import_data.py and migrate_data.py scripts")

if __name__ == "__main__":
    print("OPF Community Database - Local PostgreSQL Setup")
    print("=" * 50)
    
    success = create_local_postgresql_database()
    
    if success:
        sync_with_railway()
        
        print("\nNext steps:")
        print("1. Install PostgreSQL locally if not already installed")
        print("2. Run this script to set up local PostgreSQL")
        print("3. Use .env.local for local development")
        print("4. Use the same database type locally and in production")
    else:
        print("\nSetup failed. Please check your PostgreSQL installation.")
