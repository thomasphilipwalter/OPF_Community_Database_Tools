# OPF Community Database Management Guide

## Overview

Your OPF Community Database uses a **hybrid approach** that automatically switches between SQLite (local development) and PostgreSQL (cloud production) based on the `DATABASE_URL` environment variable.

## Current Setup

### Local Development
- **Database**: SQLite (`opf_community.db`)
- **Location**: Your local machine
- **Purpose**: Development and testing

### Cloud Production (Railway)
- **Database**: PostgreSQL
- **Location**: Railway cloud infrastructure
- **Purpose**: Live application serving users

## Recommended Approach: PostgreSQL-First Strategy

For better consistency and scalability, we recommend converting your local setup to PostgreSQL. This provides:

1. **Consistency**: Same database type locally and in production
2. **Scalability**: PostgreSQL handles larger datasets better
3. **Features**: Advanced features like full-text search, JSON support
4. **Performance**: Better performance for complex queries

## Setup Instructions

### Step 1: Install PostgreSQL Locally

**On macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**On Windows:**
Download and install from https://www.postgresql.org/download/windows/

**On Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Step 2: Set Up Local PostgreSQL Database

Run the setup script to create your local PostgreSQL database:

```bash
python setup_local_postgresql.py
```

This script will:
- Create a local PostgreSQL database (`opf_community_local`)
- Migrate your existing SQLite data
- Create a `.env.local` file for local development

### Step 3: Configure Environment Variables

The setup script creates a `.env.local` file. For local development, use:

```bash
# Load local environment variables
export $(cat .env.local | xargs)

# Or run your app with the local config
python app.py
```

## Database Synchronization

### Using the Sync Tool

We've created `sync_databases.py` to help you manage data between local and cloud databases:

```bash
python sync_databases.py
```

**Options:**
1. **Sync Railway → Local**: Pull latest data from cloud to local
2. **Sync Local → Railway**: Push local changes to cloud
3. **Compare databases**: Check if databases are in sync

### Manual Synchronization

If you prefer manual control, you can use the existing scripts:

**Export from Railway:**
```bash
python migrate_data.py  # Creates CSV exports
```

**Import to Railway:**
```bash
python import_data.py  # Imports CSV data
```

## Workflow Recommendations

### For Development
1. **Use local PostgreSQL** for development
2. **Make changes locally** first
3. **Test thoroughly** before pushing to production
4. **Sync to Railway** when ready to deploy

### For Data Management
1. **Railway as source of truth** for production data
2. **Local PostgreSQL** for development and testing
3. **Regular syncs** to keep environments in sync
4. **Backup strategy** for both environments

## Environment Configuration

### Local Development (.env.local)
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
GOOGLE_CLIENT_ID=your-google-client-id-here
DATABASE_URL=postgresql://postgres:@localhost:5432/opf_community_local
```

### Production (Railway Environment Variables)
```bash
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
GOOGLE_CLIENT_ID=your-production-google-client-id
DATABASE_URL=postgresql://... (Railway provides this)
```

## Database Schema

Both local and cloud databases use the same schema defined in `postgresql_schema.sql`:

```sql
CREATE TABLE final (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    -- ... other fields
);
```

## Best Practices

### 1. Always Backup Before Major Changes
```bash
# Export current data
python sync_databases.py  # Option 1 to export Railway data
```

### 2. Test Changes Locally First
- Make changes in local PostgreSQL
- Test thoroughly
- Sync to Railway only when ready

### 3. Use Version Control for Schema Changes
- Keep `postgresql_schema.sql` in version control
- Document any schema changes
- Apply changes to both environments

### 4. Monitor Database Performance
- Use Railway's monitoring tools
- Check query performance
- Optimize indexes as needed

## Troubleshooting

### Common Issues

**1. PostgreSQL Connection Error**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql
```

**2. Permission Issues**
```bash
# Create PostgreSQL user if needed
sudo -u postgres createuser --interactive
```

**3. Database Not Found**
```bash
# Run the setup script again
python setup_local_postgresql.py
```

**4. Sync Issues**
- Check network connectivity
- Verify Railway credentials
- Ensure both databases have the same schema

### Getting Help

1. Check the logs in Railway dashboard
2. Verify environment variables are set correctly
3. Test database connections separately
4. Use the compare function to check sync status

## Migration from SQLite

If you want to completely migrate from SQLite to PostgreSQL:

1. **Backup your SQLite data**
2. **Run the setup script** to create local PostgreSQL
3. **Verify data migration** was successful
4. **Update your workflow** to use PostgreSQL
5. **Keep SQLite as backup** until you're confident

## Advanced Features

### Full-Text Search
PostgreSQL provides better full-text search capabilities than SQLite. The schema includes a GIN index for efficient searching.

### JSON Support
PostgreSQL supports JSON fields, which can be useful for storing flexible data structures.

### Concurrent Access
PostgreSQL handles multiple concurrent users better than SQLite.

## Security Considerations

1. **Never commit sensitive data** to version control
2. **Use environment variables** for database credentials
3. **Regular backups** of both environments
4. **Monitor access** to production database
5. **Use strong passwords** for database connections

## Performance Optimization

1. **Index frequently searched columns**
2. **Use connection pooling** for production
3. **Monitor query performance**
4. **Optimize database queries**
5. **Regular maintenance** (vacuum, analyze)

---

This guide should help you manage your database effectively across both local and cloud environments. The PostgreSQL-first approach will give you better consistency and scalability for your OPF Community Database.
