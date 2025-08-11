-- Add AI Analysis columns to existing rfp_metadata table
-- Run this script to update your existing database

-- Add AI Analysis Results columns
ALTER TABLE rfp_metadata 
ADD COLUMN IF NOT EXISTS ai_fit_assessment TEXT,
ADD COLUMN IF NOT EXISTS ai_competitive_position TEXT,
ADD COLUMN IF NOT EXISTS ai_key_strengths TEXT,
ADD COLUMN IF NOT EXISTS ai_gaps_challenges TEXT,
ADD COLUMN IF NOT EXISTS ai_resource_requirements TEXT,
ADD COLUMN IF NOT EXISTS ai_risk_assessment TEXT,
ADD COLUMN IF NOT EXISTS ai_recommendations TEXT,
ADD COLUMN IF NOT EXISTS ai_analysis_date TIMESTAMP;

-- Update existing records to have NULL values for new columns
UPDATE rfp_metadata 
SET 
    ai_fit_assessment = NULL,
    ai_competitive_position = NULL,
    ai_key_strengths = NULL,
    ai_gaps_challenges = NULL,
    ai_resource_requirements = NULL,
    ai_risk_assessment = NULL,
    ai_recommendations = NULL,
    ai_analysis_date = NULL
WHERE ai_fit_assessment IS NULL;

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'rfp_metadata' 
AND column_name LIKE 'ai_%'
ORDER BY column_name;
