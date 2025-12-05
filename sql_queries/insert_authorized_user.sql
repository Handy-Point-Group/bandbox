-- Insert Authorized User
-- This template is for manually adding authorized users to an organization
-- Normally this is done through the authorized-users.py page by organization admins

-- Replace the placeholder values with actual data:
-- :email              -> Email address of the user to authorize (required)
-- :organization_id    -> UUID of the organization (required)
-- :authorized_by      -> UUID of the user who is authorizing (admin who is adding them)
-- :full_name          -> Full name of the authorized user (optional)
-- :assigned_role      -> Role to assign: 'player', 'coach', 'admin', 'admin-team', 'admin-org' (default: 'player')
-- :authorization_note -> Note about why they're being authorized (optional)

-- Full insert with all fields:
INSERT INTO public.authorized_users (
    email,
    full_name,
    organization_id,
    assigned_role,
    authorized_by,
    authorization_note,
    is_active,
    has_signed_up,
    created_at,
    updated_at
) VALUES (
    :email,                              -- e.g., 'newuser@example.com'
    :full_name,                          -- e.g., 'John Doe'
    :organization_id,                    -- e.g., 'a1b2c3d4-...' (UUID from organizations table)
    :assigned_role,                      -- e.g., 'player', 'coach', 'admin-org'
    :authorized_by,                      -- e.g., 'e5f6g7h8-...' (UUID of authorizing user from users table)
    :authorization_note,                 -- e.g., 'New team member - outfielder'
    TRUE,                                -- is_active
    FALSE,                               -- has_signed_up (will be TRUE after they sign up)
    NOW(),
    NOW()
)
RETURNING id, email, organization_id, assigned_role;

-- Example with actual values (replace with your data):
-- INSERT INTO public.authorized_users (
--     email,
--     full_name,
--     organization_id,
--     assigned_role,
--     authorized_by,
--     authorization_note,
--     is_active,
--     has_signed_up
-- ) VALUES (
--     'player@redsox.com',
--     'Mike Trout',
--     'a1b2c3d4-e5f6-7890-abcd-ef1234567890',  -- Red Sox organization ID
--     'player',
--     'e5f6g7h8-i9j0-1234-5678-901234567890',  -- Org admin user ID
--     'Star player - center field',
--     TRUE,
--     FALSE
-- )
-- RETURNING id, email, organization_id, assigned_role;

-- Simple insert with just required fields:
-- INSERT INTO public.authorized_users (
--     email,
--     organization_id,
--     assigned_role,
--     authorized_by
-- ) VALUES (
--     'user@example.com',
--     'org-uuid-here',
--     'player',
--     'admin-user-uuid-here'
-- )
-- RETURNING id, email;

-- Useful queries for checking authorized users:

-- 1. Get all authorized users for an organization:
-- SELECT * FROM public.authorized_users 
-- WHERE organization_id = 'org-uuid-here'
-- ORDER BY created_at DESC;

-- 2. Get pending signups (users who haven't signed up yet):
-- SELECT email, full_name, assigned_role, created_at
-- FROM public.authorized_users 
-- WHERE organization_id = 'org-uuid-here'
-- AND has_signed_up = FALSE
-- AND is_active = TRUE
-- ORDER BY created_at DESC;

-- 3. Get all users authorized by a specific admin:
-- SELECT au.email, au.full_name, au.assigned_role, u.full_name as authorized_by_name
-- FROM public.authorized_users au
-- LEFT JOIN public.users u ON au.authorized_by = u.id
-- WHERE au.authorized_by = 'admin-user-uuid-here'
-- ORDER BY au.created_at DESC;

-- 4. Check if a user is authorized for any organization:
-- SELECT * FROM public.authorized_users 
-- WHERE email = 'user@example.com'
-- AND is_active = TRUE
-- AND has_signed_up = FALSE;

