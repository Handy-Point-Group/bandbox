-- Create Organizations Table
-- Run this in your Supabase SQL Editor BEFORE creating the users table
-- (users table references organizations)

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    
    -- Organization type/category
    org_type TEXT DEFAULT 'team' CHECK (
        org_type IN (
            'team',
            'league',
            'club',
            'school',
            'other'
        )
    ),
    
    -- Contact information
    email TEXT,
    phone TEXT,
    website TEXT,
    
    -- Address information
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'USA',
    
    -- Organization settings
    is_active BOOLEAN DEFAULT TRUE,
    max_teams INTEGER DEFAULT 1,
    max_members INTEGER,
    
    -- Branding
    logo_url TEXT,
    primary_color TEXT,
    secondary_color TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional data
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_org_type ON organizations(org_type);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);

-- Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add helpful comments
COMMENT ON TABLE organizations IS 'Stores organization information such as teams, leagues, clubs, or schools';
COMMENT ON COLUMN organizations.name IS 'Organization name (required, used for internal reference)';
COMMENT ON COLUMN organizations.display_name IS 'Display name for the organization (can be different from name)';
COMMENT ON COLUMN organizations.org_type IS 'Type of organization: team, league, club, school, or other';
COMMENT ON COLUMN organizations.max_teams IS 'Maximum number of teams allowed in this organization';
COMMENT ON COLUMN organizations.max_members IS 'Maximum number of members allowed in this organization';
COMMENT ON COLUMN organizations.logo_url IS 'URL to the organization logo image';
COMMENT ON COLUMN organizations.metadata IS 'Additional flexible data stored as JSON';

