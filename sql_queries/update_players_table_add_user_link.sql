-- Update Players Table to support user linking and additional fields
-- Run this in your Supabase SQL Editor

-- Add user_id column to link players to users (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE players ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add email column for data matching (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'email'
    ) THEN
        ALTER TABLE players ADD COLUMN email TEXT;
    END IF;
END $$;

-- Add birthdate column (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'birthdate'
    ) THEN
        ALTER TABLE players ADD COLUMN birthdate DATE;
    END IF;
END $$;

-- Add metadata column for storing survey data and other info (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE players ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add timestamps (if they don't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE players ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'players' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE players ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_players_user_id ON players(user_id);
CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);

-- Add helpful comments
COMMENT ON COLUMN players.user_id IS 'Foreign key to users table - links player profile to user account';
COMMENT ON COLUMN players.email IS 'Email address for data matching and integration';
COMMENT ON COLUMN players.birthdate IS 'Player date of birth';
COMMENT ON COLUMN players.metadata IS 'JSON field for survey data and additional profile information';
COMMENT ON COLUMN players.created_at IS 'Timestamp when player profile was created';
COMMENT ON COLUMN players.updated_at IS 'Timestamp when player profile was last updated';

-- Add unique constraint to ensure one player profile per user (optional - comment out if you want users to have multiple profiles)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (
--         SELECT 1 FROM pg_constraint 
--         WHERE conname = 'players_user_id_unique'
--     ) THEN
--         ALTER TABLE players ADD CONSTRAINT players_user_id_unique UNIQUE(user_id);
--     END IF;
-- END $$;

