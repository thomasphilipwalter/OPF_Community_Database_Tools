# OPFA Community Database Search

A full-stack web application that allows users to search the OPFA community database for keywords or phrases across all fields in the 'final' table.

## Features

- **Full-Text Search**: Search across all columns in the database
- **Modern UI**: Clean, responsive design with Bootstrap 5
- **Real-time Results**: Instant search results with highlighting
- **Export Functionality**: Download search results as CSV
- **Database Statistics**: View database overview in the header
- **Mobile Responsive**: Works on all device sizes

## Database Structure

The application searches the `final` table with the following columns:
- `first_name`, `last_name` - Personal information
- `email`, `email_other`, `linkedin` - Contact information
- `city`, `country` - Location data
- `current_job`, `current_company` - Professional information
- `linkedin_summary`, `resume`, `executive_summary` - Professional summaries
- `years_xp`, `years_sustainability_xp` - Experience levels
- `linkedin_skills`, `key_competencies`, `key_sectors` - Skills and expertise
- `gender_identity`, `race_ethnicity`, `lgbtqia` - Demographic information
- `source` - Data source information

## Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have the following files in your directory:
   # - app.py
   # - opfa_community.db
   # - requirements.txt
   # - templates/index.html
   # - static/css/style.css
   # - static/js/app.js
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your web browser and go to: `http://localhost:5000`

## Usage

### Basic Search
1. Enter a keyword or phrase in the search box
2. Click "Search" or press Enter
3. View results displayed in cards

### Search Examples
- **Names**: "Jared", "Shannon", "Alex"
- **Companies**: "Antea Group", "Persefoni", "Agenda"
- **Skills**: "sustainability", "consultant", "ESG"
- **Locations**: "Denver", "Chicago", "United States"
- **Job Titles**: "Manager", "Consultant", "Sustainability"

### Features
- **Highlighted Results**: Search terms are highlighted in yellow
- **Export Results**: Download current search results as CSV
- **Clear Results**: Reset the search and results
- **Database Stats**: View total records and key metrics

## Technical Details

### Backend (Python Flask)
- **Framework**: Flask 2.3.3
- **Database**: SQLite3 (opfa_community.db)
- **Search**: Case-insensitive LIKE queries across all columns
- **API Endpoints**:
  - `GET /` - Main application page
  - `POST /search` - Search database
  - `GET /api/stats` - Get database statistics

### Frontend (HTML/CSS/JavaScript)
- **Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Responsive Design**: Mobile-first approach
- **Interactive Features**: Real-time search, export, highlighting

### Search Algorithm
The application performs case-insensitive searches across all columns using SQL LIKE queries:
```sql
SELECT * FROM final 
WHERE LOWER(column1) LIKE LOWER('%keyword%') 
   OR LOWER(column2) LIKE LOWER('%keyword%')
   OR ...
ORDER BY first_name, last_name
```

## File Structure
```
Key_Word_App/
├── app.py                 # Main Flask application
├── opfa_community.db     # SQLite database
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/
│   └── index.html       # Main HTML template
└── static/
    ├── css/
    │   └── style.css    # Custom CSS styles
    └── js/
        └── app.js       # Frontend JavaScript
```

## Troubleshooting

### Common Issues

1. **Database not found**
   - Ensure `opfa_community.db` is in the same directory as `app.py`

2. **Port already in use**
   - Change the port in `app.py` line 95: `app.run(debug=True, host='0.0.0.0', port=5001)`

3. **Python dependencies not installed**
   - Run: `pip install -r requirements.txt`

4. **No results found**
   - Try different keywords or partial matches
   - Check spelling and case sensitivity

### Performance Notes
- The database is ~37MB with multiple records
- Search performance depends on database size and query complexity
- Results are limited to prevent overwhelming the UI

## Security Considerations
- The application runs locally and doesn't expose the database externally
- Search queries are sanitized to prevent SQL injection
- No sensitive data is logged or stored outside the database

## Future Enhancements
- Advanced search filters (by location, experience level, etc.)
- Pagination for large result sets
- Search history and saved searches
- Advanced analytics and reporting
- User authentication and access control 