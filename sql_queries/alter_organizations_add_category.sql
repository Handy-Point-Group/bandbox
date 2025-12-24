-- Add organization category and sub-type columns
-- Run this in your Supabase SQL Editor

-- Add organization category (Training vs Competitive)
ALTER TABLE public.organizations 
ADD COLUMN IF NOT EXISTS org_category TEXT CHECK (
    org_category IN ('training', 'competitive')
);

-- Add organization sub-type
ALTER TABLE public.organizations 
ADD COLUMN IF NOT EXISTS org_subtype TEXT;

-- Add constraint for sub-types based on category
-- Training sub-types: facility, personal_trainer, scouting
-- Competitive sub-types: travel, high_school, college_d1, college_d2, college_d3, juco, summer_league, independent, youth, other
ALTER TABLE public.organizations
ADD CONSTRAINT check_org_subtype CHECK (
    (org_category = 'training' AND org_subtype IN ('facility', 'personal_trainer', 'scouting', 'other')) OR
    (org_category = 'competitive' AND org_subtype IN ('travel', 'high_school', 'college_d1', 'college_d2', 'college_d3', 'juco', 'summer_league', 'independent', 'youth', 'other')) OR
    (org_category IS NULL)
);

-- Add column to track if organization has teams
ALTER TABLE public.organizations 
ADD COLUMN IF NOT EXISTS has_teams BOOLEAN DEFAULT TRUE;

-- Update existing organizations to have a category (default to competitive for teams)
UPDATE public.organizations 
SET org_category = 'competitive', has_teams = TRUE 
WHERE org_category IS NULL AND org_type IN ('team', 'league', 'club');

UPDATE public.organizations 
SET org_category = 'training', has_teams = FALSE 
WHERE org_category IS NULL AND org_type IN ('school', 'other');

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_category ON public.organizations(org_category);
CREATE INDEX IF NOT EXISTS idx_organizations_subtype ON public.organizations(org_subtype);

-- Add comments
COMMENT ON COLUMN public.organizations.org_category IS 'Organization category: training (no teams) or competitive (has teams)';
COMMENT ON COLUMN public.organizations.org_subtype IS 'Sub-type within category (e.g., facility, travel, high_school)';
COMMENT ON COLUMN public.organizations.has_teams IS 'Whether this organization has teams (competitive) or is team-less (training)';
