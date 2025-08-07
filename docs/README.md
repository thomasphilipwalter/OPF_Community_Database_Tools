# OPF Community Database

A Flask application for managing and searching the OPF community database.

## Project Structure

```
OPF_Community_Database_Tools/
├── app/                    # Main application package
│   ├── routes/            # Route handlers
│   ├── services/          # Business logic
│   ├── utils/             # Utility functions
│   └── config/            # Configuration
├── scripts/               # Database management scripts
├── static/                # Static assets (CSS, JS, images)
├── templates/             # HTML templates
├── tests/                 # Test files
└── docs/                  # Documentation
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   GOOGLE_CLIENT_ID=your-google-client-id
   SECRET_KEY=your-secret-key
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

## Database Management

### Local Development
- Use PostgreSQL for local development
- Database scripts are in the `scripts/` directory

### Production (Railway)
- PostgreSQL database hosted on Railway
- Automatic deployment from main branch

## Features

- **Google OAuth Authentication** - @opf.degree domain only
- **Advanced Search** - Keyword-based search with filters
- **RFP Analysis** - Upload and analyze RFP documents
- **Resume Display** - Enhanced resume viewing with formatting
- **Database Management** - Tools for syncing local and production data

## Development

### Running Locally
```bash
python run.py
```

### Database Scripts
```bash
# Download Railway data
python scripts/download_railway_db.py

# Convert CSV to local PostgreSQL
python scripts/csv_to_postgresql.py

# Sync local changes to Railway
python scripts/migrate_data_local_to_remote.py
```

## Deployment

The application is automatically deployed to Railway when changes are pushed to the main branch.

## Testing

Run tests with:
```bash
python -m pytest tests/
```
