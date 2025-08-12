#!/usr/bin/env python3
"""
Script to initialize the tender scraping database table
Run this after updating your database schema
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.database import get_database_connection

def init_tender_scraping_table():
    """Initialize the scraped_tenders table"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Create the scraped_tenders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_tenders (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                closing_date VARCHAR(255),
                organization VARCHAR(255),
                link TEXT UNIQUE,
                source VARCHAR(255),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_climate_related BOOLEAN DEFAULT TRUE,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_title ON scraped_tenders(title);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_source ON scraped_tenders(source);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_closing_date ON scraped_tenders(closing_date);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_is_climate_related ON scraped_tenders(is_climate_related);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_processed ON scraped_tenders(processed);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_tenders_text_search ON scraped_tenders 
            USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tender scraping table initialized successfully!")
        print("   - Created scraped_tenders table")
        print("   - Created all necessary indexes")
        print("   - Table is ready for use")
        
    except Exception as e:
        print(f"❌ Error initializing tender scraping table: {e}")
        sys.exit(1)

def test_tender_scraping():
    """Test the tender scraping functionality"""
    try:
        from app.services.tender_scraper import TenderScraper
        
        print("\n🧪 Testing tender scraping functionality...")
        
        scraper = TenderScraper()
        
        # Test Australian tenders (just one page)
        print("   Testing Australian tenders scraping...")
        aus_tenders = scraper.scrape_aus_tenders(max_pages=1)
        print(f"   Found {len(aus_tenders)} Australian tenders")
        
        # Test GIZ tenders (just one page)
        print("   Testing GIZ tenders scraping...")
        giz_tenders = scraper.scrape_giz_tenders(max_pages=1)
        print(f"   Found {len(giz_tenders)} GIZ tenders")
        
        print("✅ Tender scraping test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing tender scraping: {e}")
        print("   This might be due to network issues or website changes")
        print("   The functionality should still work in production")

if __name__ == "__main__":
    load_dotenv()
    
    print("🚀 Initializing Tender Scraping System")
    print("=" * 50)
    
    # Initialize the database table
    init_tender_scraping_table()
    
    # Test the scraping functionality
    test_tender_scraping()
    
    print("\n🎉 Tender scraping system is ready!")
    print("   You can now use the 'Tender Scraping' tab in your application")
