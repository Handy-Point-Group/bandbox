-- Create Authorized Users Table
-- This table tracks users who are pre-authorized to join specific organizations
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.authorized_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User identification
    email TEXT NOT NULL,
    full_name TEXT,
    
    -- Organization association
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Pre-assigned role for when they sign up
    assigned_role TEXT NOT NULL DEFAULT 'player' CHECK (
        assigned_role IN (
            'superadmin', 
            'admin-org', 
            'admin-team', 
            'admin', 
            'coach', 
            'player', 
            'user'
        )
    ),
    
    -- Authorization details
    authorized_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    authorization_note TEXT,
    
    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE,
    has_signed_up BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Invitation details
    invitation_sent_at TIMESTAMP WITH TIME ZONE,
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    signed_up_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure one authorization per email per organization
    UNIQUE(email, organization_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_authorized_users_email ON public.authorized_users(email);
CREATE INDEX IF NOT EXISTS idx_authorized_users_organization ON public.authorized_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_authorized_users_status ON public.authorized_users(has_signed_up, is_active);
CREATE INDEX IF NOT EXISTS idx_authorized_users_user_id ON public.authorized_users(user_id);

-- Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_authorized_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_authorized_users_updated_at ON public.authorized_users;
CREATE TRIGGER update_authorized_users_updated_at
    BEFORE UPDATE ON public.authorized_users
    FOR EACH ROW
    EXECUTE FUNCTION update_authorized_users_updated_at();

-- Add helpful comments
COMMENT ON TABLE public.authorized_users IS 'Tracks users who are pre-authorized to join specific organizations';
COMMENT ON COLUMN public.authorized_users.email IS 'Email address of the authorized user';
COMMENT ON COLUMN public.authorized_users.organization_id IS 'Organization the user is authorized to join';
COMMENT ON COLUMN public.authorized_users.assigned_role IS 'Role that will be assigned when user signs up';
COMMENT ON COLUMN public.authorized_users.authorized_by IS 'User ID of the person who authorized this user';
COMMENT ON COLUMN public.authorized_users.has_signed_up IS 'Whether the user has completed signup';
COMMENT ON COLUMN public.authorized_users.user_id IS 'Link to actual user record once they sign up';
COMMENT ON COLUMN public.authorized_users.invitation_sent_at IS 'When invitation email was sent';
COMMENT ON COLUMN public.authorized_users.invitation_expires_at IS 'When the invitation expires';

-- Example: Add an authorized user
-- INSERT INTO public.authorized_users (
--     email,
--     full_name,
--     organization_id,
--     assigned_role,
--     authorized_by
-- ) VALUES (
--     'newuser@example.com',
--     'John Doe',
--     'org-uuid-here',
--     'player',
--     'admin-user-uuid-here'
-- );

