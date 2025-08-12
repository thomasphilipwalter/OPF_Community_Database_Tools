# Tender Scraping System

The Tender Scraping system automatically collects Request for Proposals (RFPs) and tenders from various government and organization websites, specifically focusing on climate, sustainability, and environment-related projects.

## Features

- **Automated Scraping**: Scrapes tender databases daily for new opportunities
- **Climate Focus**: Automatically filters for climate/sustainability/environment projects
- **Multiple Sources**: Currently supports:
  - Australian Government Tenders (tenders.gov.au)
  - GIZ (German Development Agency) tenders
- **Smart Filtering**: Uses keyword matching to identify relevant projects
- **Database Storage**: Stores all scraped tenders with metadata
- **Processing Workflow**: Mark tenders as processed/unprocessed
- **Search & Filter**: Find tenders by source, status, and other criteria

## Setup

### 1. Install Dependencies

The system requires additional Python packages for web scraping:

```bash
pip install beautifulsoup4 lxml selenium webdriver-manager schedule
```

Or update your requirements.txt and run:

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Run the initialization script to create the required database table:

```bash
cd scripts
python init_tender_scraping.py
```

This will:
- Create the `scraped_tenders` table
- Set up all necessary indexes
- Test the scraping functionality

### 3. Database Schema

The system creates a `scraped_tenders` table with the following structure:

```sql
CREATE TABLE scraped_tenders (
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
```

## Usage

### Web Interface

1. **Access the Tab**: Click on the "Tender Scraping" tab in your application
2. **Start Scraping**: Click the "Start Scraping" button to begin collecting tenders
3. **View Results**: Browse scraped tenders in the list below
4. **Filter Tenders**: Use the filter buttons to view All/Unprocessed/Processed tenders
5. **Mark as Processed**: Click the checkmark button to mark tenders as processed

### API Endpoints

The system provides several API endpoints for programmatic access:

#### Scrape Tenders
```http
POST /api/tenders/scrape
```
Starts the scraping process for all configured sources.

#### List Tenders
```http
GET /api/tenders/list?source={source}&processed={true|false}&limit={limit}&offset={offset}
```
Retrieves a list of scraped tenders with optional filtering.

#### Get Statistics
```http
GET /api/tenders/stats
```
Returns statistics about scraped tenders including counts by source and recent activity.

#### Mark as Processed
```http
POST /api/tenders/mark-processed
Content-Type: application/json

{
    "tender_id": 123,
    "processed": true
}
```
Marks a tender as processed or unprocessed.

## Configuration

### Climate Keywords

The system automatically filters tenders using these keywords:

- **Climate**: climate, sustainability, environment, environmental
- **Energy**: green, renewable, energy, carbon, emissions
- **Nature**: biodiversity, conservation, ecosystem, forest, ocean, marine
- **Resources**: waste, recycling, pollution, water, air quality, soil
- **Agriculture**: agriculture, food security, habitat, wildlife
- **Adaptation**: adaptation, mitigation

### Scraping Sources

#### Australian Government Tenders
- **URL**: https://www.tenders.gov.au/atm
- **Scope**: Government contracts and tenders
- **Pages**: Configurable (default: 5 pages)
- **Rate Limiting**: 1 second delay between requests

#### GIZ (German Development Agency)
- **URL**: https://ausschreibungen.giz.de/
- **Scope**: International development projects
- **Pages**: Configurable (default: 5 pages)
- **Rate Limiting**: 1 second delay between requests

## Adding New Sources

To add new tender sources:

1. **Create Scraper Method**: Add a new method to `TenderScraper` class
2. **Update Main Scraping**: Add the new source to `scrape_all_sources()`
3. **Add to Database**: Ensure the source name is properly stored
4. **Test**: Run the initialization script to test the new source

Example:

```python
def scrape_new_source(self, max_pages: int = 5) -> List[Dict]:
    """Scrape tenders from new source"""
    tenders = []
    # Implementation here
    return tenders
```

## Monitoring & Maintenance

### Daily Scraping

The system is designed to run daily to collect new tenders. You can:

1. **Manual Scraping**: Use the web interface to scrape on demand
2. **Automated Scraping**: Set up a cron job or scheduler
3. **Monitoring**: Check the dashboard for scraping statistics

### Data Management

- **Storage**: All tenders are stored in the database with unique links
- **Updates**: Existing tenders are updated if re-scraped
- **Cleanup**: Consider implementing a retention policy for old tenders

### Performance

- **Rate Limiting**: Built-in delays to respect website policies
- **Error Handling**: Graceful handling of network issues and parsing errors
- **Logging**: Comprehensive logging for debugging and monitoring

## Troubleshooting

### Common Issues

1. **No Tenders Found**: Check if websites have changed their structure
2. **Scraping Errors**: Verify network connectivity and website availability
3. **Database Errors**: Ensure the database table is properly initialized

### Debugging

- Check the application logs for detailed error messages
- Use the test functionality in the initialization script
- Verify database connectivity and permissions

## Security & Compliance

- **Rate Limiting**: Respects website terms of service
- **User Agents**: Uses realistic browser user agents
- **Data Privacy**: Only stores publicly available tender information
- **Access Control**: Requires user authentication for all operations

## Future Enhancements

Potential improvements for the system:

- **More Sources**: Add additional government and organization websites
- **Advanced Filtering**: Machine learning-based relevance scoring
- **Notifications**: Email alerts for new relevant tenders
- **Export**: CSV/Excel export of tender data
- **Analytics**: Dashboard with trends and insights
- **Integration**: Connect with RFP analysis system

## Support

For issues or questions about the tender scraping system:

1. Check the application logs
2. Verify database setup
3. Test individual scraping sources
4. Review the configuration and keywords
