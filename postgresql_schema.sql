
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

-- RFP Tables
-- Create the rfp_metadata table (parent table for RFP projects)
CREATE TABLE IF NOT EXISTS rfp_metadata (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255),
    due_date DATE,
    organization_group VARCHAR(255),
    link TEXT,
    country VARCHAR(100),
    project_focus TEXT,
    region VARCHAR(100),
    industry VARCHAR(100),
    opf_gap_size VARCHAR(50),
    opf_gaps TEXT,
    deliverables TEXT,
    posting_contact VARCHAR(255),
    potential_experts TEXT,
    project_cost DECIMAL(15,2),
    currency VARCHAR(50),
    specific_staffing_needs TEXT,
    -- AI Analysis Results
    ai_fit_assessment TEXT,
    ai_competitive_position TEXT,
    ai_key_strengths TEXT,
    ai_gaps_challenges TEXT,
    ai_resource_requirements TEXT,
    ai_risk_assessment TEXT,
    ai_recommendations TEXT,
    ai_analysis_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the documents table (child table for RFP documents)
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    rfp_id INTEGER NOT NULL REFERENCES rfp_metadata(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    document_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for RFP tables
CREATE INDEX IF NOT EXISTS idx_rfp_metadata_project_name ON rfp_metadata(project_name);
CREATE INDEX IF NOT EXISTS idx_rfp_metadata_organization_group ON rfp_metadata(organization_group);
CREATE INDEX IF NOT EXISTS idx_rfp_metadata_country ON rfp_metadata(country);
CREATE INDEX IF NOT EXISTS idx_rfp_metadata_due_date ON rfp_metadata(due_date);
CREATE INDEX IF NOT EXISTS idx_documents_rfp_id ON documents(rfp_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_name ON documents(document_name);

-- Add a full-text search index for document content
CREATE INDEX IF NOT EXISTS idx_documents_text_search ON documents USING gin(to_tsvector('english', document_text));
