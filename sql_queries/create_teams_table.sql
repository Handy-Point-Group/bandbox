-- Create Teams Table
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to organization
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Basic Information
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    
    -- Team Classification
    age_group TEXT,  -- e.g., "14U", "16U", "18U", "Varsity", "JV", "Freshman"
    level TEXT CHECK (level IN ('varsity', 'jv', 'freshman', 'travel_a', 'travel_b', 'rec', 'showcase', 'other')),
    season TEXT,  -- e.g., "Spring 2025", "Fall 2024"
    year INTEGER,
    
    -- Head Coach
    head_coach_id UUID REFERENCES public.coaches(id) ON DELETE SET NULL,
    
    -- Branding (inherits from org if not set)
    logo_url TEXT,
    primary_color TEXT,
    secondary_color TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional data
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team_coaches junction table for assistant coaches
CREATE TABLE IF NOT EXISTS public.team_coaches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    coach_id UUID NOT NULL REFERENCES public.coaches(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'assistant',  -- head, assistant, pitching, hitting, etc.
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(team_id, coach_id)
);

-- Create team_players junction table
CREATE TABLE IF NOT EXISTS public.team_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES public.players2(id) ON DELETE CASCADE,
    jersey_number INTEGER,
    position TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(team_id, player_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_teams_organization_id ON public.teams(organization_id);
CREATE INDEX IF NOT EXISTS idx_teams_head_coach_id ON public.teams(head_coach_id);
CREATE INDEX IF NOT EXISTS idx_teams_is_active ON public.teams(is_active);
CREATE INDEX IF NOT EXISTS idx_team_coaches_team_id ON public.team_coaches(team_id);
CREATE INDEX IF NOT EXISTS idx_team_coaches_coach_id ON public.team_coaches(coach_id);
CREATE INDEX IF NOT EXISTS idx_team_players_team_id ON public.team_players(team_id);
CREATE INDEX IF NOT EXISTS idx_team_players_player_id ON public.team_players(player_id);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_teams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_teams_updated_at ON public.teams;
CREATE TRIGGER trigger_teams_updated_at
    BEFORE UPDATE ON public.teams
    FOR EACH ROW
    EXECUTE FUNCTION update_teams_updated_at();

-- Add comments
COMMENT ON TABLE public.teams IS 'Teams within organizations';
COMMENT ON COLUMN public.teams.organization_id IS 'Parent organization';
COMMENT ON COLUMN public.teams.age_group IS 'Age group like 14U, 16U, Varsity';
COMMENT ON COLUMN public.teams.level IS 'Competition level';
COMMENT ON COLUMN public.teams.head_coach_id IS 'Primary head coach';
COMMENT ON TABLE public.team_coaches IS 'Junction table for team coaching staff';
COMMENT ON TABLE public.team_players IS 'Junction table for team rosters';

-- Create view for teams with coach names
CREATE OR REPLACE VIEW public.teams_with_details AS
SELECT 
    t.*,
    o.name AS organization_name,
    c.first_name || ' ' || c.last_name AS head_coach_name
FROM public.teams t
LEFT JOIN public.organizations o ON t.organization_id = o.id
LEFT JOIN public.coaches c ON t.head_coach_id = c.id;
