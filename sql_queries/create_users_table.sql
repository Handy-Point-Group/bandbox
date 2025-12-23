-- Create Users Table (Revised for new roles, multi-org/team support, new fields)
-- Run this in your Supabase SQL Editor AFTER creating the organizations table

CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    google_id TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT NOT NULL,

    -- Organizations
    primary_organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    multi_org BOOLEAN DEFAULT FALSE,
    organization_ids UUID[] DEFAULT NULL,

    -- Teams
    multi_team BOOLEAN DEFAULT FALSE,
    team_ids UUID[] DEFAULT NULL,

    -- Link to player profile (if user is a player)
    player_id INTEGER REFERENCES public.players(id) ON DELETE SET NULL,

    role TEXT NOT NULL DEFAULT 'user' CHECK (
        role IN (
            'superadmin', 
            'admin-org', 
            'admin-team', 
            'admin', 
            'coach', 
            'player', 
            'user'
        )
    ),
    birthdate DATE,
    privacy_agreement_link TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON public.users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_primary_organization ON public.users(primary_organization_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);
CREATE INDEX IF NOT EXISTS idx_users_player_id ON public.users(player_id);

-- Add helpful comments
COMMENT ON TABLE public.users IS 'Stores user authentication and profile information, with support for multiple organizations and teams, and detailed roles';
COMMENT ON COLUMN public.users.email IS 'User email address (unique)';
COMMENT ON COLUMN public.users.google_id IS 'Google OAuth user ID for Google login';
COMMENT ON COLUMN public.users.password_hash IS 'Bcrypt hashed password for email/password login';
COMMENT ON COLUMN public.users.role IS 'User role: user < player < coach < admin < admin-team < admin-org < superadmin';
COMMENT ON COLUMN public.users.primary_organization_id IS 'Primary organization of the user, foreign key to organizations table';
COMMENT ON COLUMN public.users.multi_org IS 'Flag indicating if user belongs to multiple organizations';
COMMENT ON COLUMN public.users.organization_ids IS 'Array of organization IDs if multi_org is true';
COMMENT ON COLUMN public.users.multi_team IS 'Flag indicating if user belongs to multiple teams';
COMMENT ON COLUMN public.users.team_ids IS 'Array of team IDs if multi_team is true';
COMMENT ON COLUMN public.users.birthdate IS 'Date of birth of the user';
COMMENT ON COLUMN public.users.privacy_agreement_link IS 'URL to the privacy agreement the user consented to';
COMMENT ON COLUMN public.users.player_id IS 'Foreign key linking user to their player profile in the players table';

