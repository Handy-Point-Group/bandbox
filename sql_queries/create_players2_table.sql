-- Create Players2 Table (Enhanced player profiles with bio information)
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.players2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to user account (optional - player may not have an account yet)
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Link to organization
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Basic Information
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    
    -- Baseball Info
    jersey_number INTEGER,
    primary_position TEXT CHECK (primary_position IN ('C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'OF', 'P', 'DH', 'UT')),
    secondary_position TEXT CHECK (secondary_position IN ('C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'OF', 'P', 'DH', 'UT')),
    tertiary_position TEXT CHECK (tertiary_position IN ('C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'OF', 'P', 'DH', 'UT')),
    is_pitcher BOOLEAN DEFAULT FALSE,
    batting_hand TEXT CHECK (batting_hand IN ('R', 'L', 'S')),  -- R=Right, L=Left, S=Switch
    throwing_hand TEXT CHECK (throwing_hand IN ('R', 'L')),
    
    -- Physical Attributes
    height_inches INTEGER,  -- Store in inches for easy math (e.g., 72 = 6'0")
    weight_lbs INTEGER,
    
    -- Academic/Class Info
    graduation_year INTEGER,
    class_level TEXT CHECK (class_level IN ('Freshman', 'Sophomore', 'Junior', 'Senior', 'Grad', 'Middle School', 'Other')),
    high_school TEXT,
    college TEXT,
    gpa DECIMAL(3,2),
    
    -- Personal Info
    birthdate DATE,
    hometown TEXT,
    state TEXT,
    country TEXT DEFAULT 'USA',
    
    -- Bio & Social
    bio TEXT,  -- Player's personal bio/about text
    profile_photo_url TEXT,
    instagram_handle TEXT,
    twitter_handle TEXT,
    
    -- Parent/Guardian Info (for minors)
    parent_guardian_name TEXT,
    parent_guardian_email TEXT,
    parent_guardian_phone TEXT,
    
    -- External IDs (for data integrations)
    rapsodo_id TEXT,
    diamond_kinetics_id TEXT,
    trackman_id TEXT,
    
    -- Status & Metadata
    is_active BOOLEAN DEFAULT TRUE,
    roster_status TEXT DEFAULT 'active' CHECK (roster_status IN ('active', 'injured', 'inactive', 'alumni', 'prospect')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_players2_user_id ON public.players2(user_id);
CREATE INDEX IF NOT EXISTS idx_players2_organization_id ON public.players2(organization_id);
CREATE INDEX IF NOT EXISTS idx_players2_email ON public.players2(email);
CREATE INDEX IF NOT EXISTS idx_players2_last_name ON public.players2(last_name);
CREATE INDEX IF NOT EXISTS idx_players2_graduation_year ON public.players2(graduation_year);
CREATE INDEX IF NOT EXISTS idx_players2_is_active ON public.players2(is_active);
CREATE INDEX IF NOT EXISTS idx_players2_primary_position ON public.players2(primary_position);

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_players2_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_players2_updated_at ON public.players2;
CREATE TRIGGER trigger_players2_updated_at
    BEFORE UPDATE ON public.players2
    FOR EACH ROW
    EXECUTE FUNCTION update_players2_updated_at();

-- Add helpful comments
COMMENT ON TABLE public.players2 IS 'Enhanced player profiles with bio information and external integrations';
COMMENT ON COLUMN public.players2.user_id IS 'Link to user account if player has registered';
COMMENT ON COLUMN public.players2.organization_id IS 'Organization/team the player belongs to';
COMMENT ON COLUMN public.players2.batting_hand IS 'R=Right, L=Left, S=Switch hitter';
COMMENT ON COLUMN public.players2.throwing_hand IS 'R=Right, L=Left';
COMMENT ON COLUMN public.players2.height_inches IS 'Height stored in inches (e.g., 72 = 6 feet)';
COMMENT ON COLUMN public.players2.class_level IS 'Academic class level';
COMMENT ON COLUMN public.players2.roster_status IS 'Current roster status: active, injured, inactive, alumni, prospect';
COMMENT ON COLUMN public.players2.rapsodo_id IS 'External Rapsodo player ID for data integration';
COMMENT ON COLUMN public.players2.diamond_kinetics_id IS 'External Diamond Kinetics player ID';
COMMENT ON COLUMN public.players2.trackman_id IS 'External TrackMan player ID';
COMMENT ON COLUMN public.players2.metadata IS 'Additional flexible data stored as JSON';

-- Create a view for easy full name access
CREATE OR REPLACE VIEW public.players2_with_full_name AS
SELECT 
    *,
    first_name || ' ' || last_name AS full_name,
    CASE 
        WHEN height_inches IS NOT NULL THEN 
            (height_inches / 12)::TEXT || '''' || (height_inches % 12)::TEXT || '"'
        ELSE NULL
    END AS height_formatted
FROM public.players2;

-- Enable Row Level Security (optional - uncomment if needed)
-- ALTER TABLE public.players2 ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (uncomment and modify as needed)
-- CREATE POLICY "Users can view players in their organization"
--     ON public.players2
--     FOR SELECT
--     USING (organization_id IN (
--         SELECT primary_organization_id FROM public.users WHERE id = auth.uid()
--     ));
