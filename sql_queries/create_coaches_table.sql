-- Create Coaches Table (Coach profiles with bio and contact information)
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.coaches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to user account
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Link to organization
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Basic Information
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    
    -- Role & Title
    title TEXT,  -- e.g., "Head Coach", "Assistant Coach", "Pitching Coach", "Hitting Coach"
    role_type TEXT CHECK (role_type IN ('head_coach', 'assistant_coach', 'pitching_coach', 'hitting_coach', 'catching_coach', 'infield_coach', 'outfield_coach', 'strength_coach', 'volunteer', 'other')),
    years_coaching INTEGER,
    
    -- Certifications & Background
    certifications TEXT,  -- e.g., "USA Baseball Level 1, CPR Certified"
    playing_experience TEXT,  -- Brief description of playing background
    coaching_philosophy TEXT,  -- Coach's philosophy/approach
    
    -- Contact Preferences
    preferred_contact_method TEXT CHECK (preferred_contact_method IN ('email', 'phone', 'text', 'any')),
    available_hours TEXT,  -- e.g., "Weekdays 4-8pm, Weekends"
    
    -- Emergency Contact
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    
    -- Bio & Social
    bio TEXT,  -- Coach's bio/about text
    profile_photo_url TEXT,
    linkedin_url TEXT,
    
    -- Status & Metadata
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_coaches_user_id ON public.coaches(user_id);
CREATE INDEX IF NOT EXISTS idx_coaches_organization_id ON public.coaches(organization_id);
CREATE INDEX IF NOT EXISTS idx_coaches_email ON public.coaches(email);
CREATE INDEX IF NOT EXISTS idx_coaches_last_name ON public.coaches(last_name);
CREATE INDEX IF NOT EXISTS idx_coaches_is_active ON public.coaches(is_active);
CREATE INDEX IF NOT EXISTS idx_coaches_role_type ON public.coaches(role_type);

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_coaches_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_coaches_updated_at ON public.coaches;
CREATE TRIGGER trigger_coaches_updated_at
    BEFORE UPDATE ON public.coaches
    FOR EACH ROW
    EXECUTE FUNCTION update_coaches_updated_at();

-- Add helpful comments
COMMENT ON TABLE public.coaches IS 'Coach profiles with contact information and credentials';
COMMENT ON COLUMN public.coaches.user_id IS 'Link to user account if coach has registered';
COMMENT ON COLUMN public.coaches.organization_id IS 'Organization/team the coach belongs to';
COMMENT ON COLUMN public.coaches.title IS 'Official title like Head Coach, Assistant Coach, etc.';
COMMENT ON COLUMN public.coaches.role_type IS 'Type of coaching role';
COMMENT ON COLUMN public.coaches.certifications IS 'Coaching certifications and credentials';
COMMENT ON COLUMN public.coaches.playing_experience IS 'Brief playing background';
COMMENT ON COLUMN public.coaches.coaching_philosophy IS 'Coaching approach and philosophy';
COMMENT ON COLUMN public.coaches.preferred_contact_method IS 'How the coach prefers to be contacted';
COMMENT ON COLUMN public.coaches.metadata IS 'Additional flexible data stored as JSON';

-- Create a view for easy full name access
CREATE OR REPLACE VIEW public.coaches_with_full_name AS
SELECT 
    *,
    first_name || ' ' || last_name AS full_name
FROM public.coaches;

-- Enable Row Level Security (optional - uncomment if needed)
-- ALTER TABLE public.coaches ENABLE ROW LEVEL SECURITY;
