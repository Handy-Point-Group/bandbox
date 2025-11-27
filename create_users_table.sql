-- Create Users Table
-- Run this in your Supabase SQL Editor

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    google_id TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'coach', 'player', 'user')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);

-- Add helpful comments
COMMENT ON TABLE users IS 'Stores user authentication and profile information';
COMMENT ON COLUMN users.email IS 'User email address (unique)';
COMMENT ON COLUMN users.google_id IS 'Google OAuth user ID for Google login';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password for email/password login';
COMMENT ON COLUMN users.role IS 'User role: user < player < coach < admin';
COMMENT ON COLUMN users.organization_id IS 'Foreign key to organizations table';

