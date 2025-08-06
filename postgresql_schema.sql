
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
