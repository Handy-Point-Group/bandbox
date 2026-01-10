-- Create Glossary Terms Table
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.glossary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identifiers
    api_name TEXT NOT NULL UNIQUE,
    term TEXT NOT NULL,

    -- Metadata
    unit TEXT,
    source_table TEXT,

    -- Definitions
    sentence_definition TEXT,
    paragraph_definition TEXT,

    -- Status / extensibility
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);