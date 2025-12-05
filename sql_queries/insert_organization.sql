-- Insert Organization Template
-- This is a template SQL query for manually inserting an organization
-- For automated insertion with full UI, use the superadmin-organizations.py page

-- Replace the placeholder values with actual data:
-- :name              -> Organization name (required)
-- :display_name      -> Display name (optional)
-- :description       -> Organization description (optional)
-- :org_type          -> Type: 'team', 'league', 'club', 'school', 'other' (default: 'team')
-- :email             -> Contact email (optional)
-- :phone             -> Phone number (optional)
-- :website           -> Website URL (optional)
-- :address_line1     -> Address line 1 (optional)
-- :address_line2     -> Address line 2 (optional)
-- :city              -> City (optional)
-- :state             -> State/Province (optional)
-- :postal_code       -> Postal/ZIP code (optional)
-- :country           -> Country (default: 'USA')
-- :max_teams         -> Maximum teams (default: 1)
-- :max_members       -> Maximum members (optional, NULL = unlimited)
-- :logo_url          -> Logo image URL (optional)
-- :primary_color     -> Primary brand color (optional)
-- :secondary_color   -> Secondary brand color (optional)

-- Full insert with all fields:
INSERT INTO public.organizations (
    name,
    display_name,
    description,
    org_type,
    email,
    phone,
    website,
    address_line1,
    address_line2,
    city,
    state,
    postal_code,
    country,
    is_active,
    max_teams,
    max_members,
    logo_url,
    primary_color,
    secondary_color,
    created_at,
    updated_at
) VALUES (
    :name,                    -- e.g., 'Red Sox Baseball Club'
    :display_name,            -- e.g., 'Boston Red Sox'
    :description,             -- e.g., 'Professional baseball organization'
    :org_type,                -- e.g., 'team'
    :email,                   -- e.g., 'contact@redsox.com'
    :phone,                   -- e.g., '+1 (617) 555-1234'
    :website,                 -- e.g., 'https://www.redsox.com'
    :address_line1,           -- e.g., '4 Jersey Street'
    :address_line2,           -- e.g., 'Suite 100'
    :city,                    -- e.g., 'Boston'
    :state,                   -- e.g., 'MA'
    :postal_code,             -- e.g., '02215'
    :country,                 -- e.g., 'USA'
    TRUE,                     -- is_active
    :max_teams,               -- e.g., 5
    :max_members,             -- e.g., 100 or NULL for unlimited
    :logo_url,                -- e.g., 'https://example.com/logo.png'
    :primary_color,           -- e.g., '#BD3039'
    :secondary_color,         -- e.g., '#0C2340'
    NOW(),
    NOW()
)
RETURNING id, name, display_name, org_type, created_at;

-- Simple insert with just required fields:
-- INSERT INTO public.organizations (
--     name,
--     org_type,
--     is_active,
--     created_at,
--     updated_at
-- ) VALUES (
--     'My Organization',
--     'team',
--     TRUE,
--     NOW(),
--     NOW()
-- )
-- RETURNING id, name, org_type, created_at;

