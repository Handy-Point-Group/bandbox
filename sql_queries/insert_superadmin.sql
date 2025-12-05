-- Insert Superadmin User
-- This is a template SQL query for manually inserting a superadmin user
-- For automated insertion with password hashing, use the create_superadmin.py script instead

-- Replace the placeholder values with actual data:
-- :email          -> The superadmin's email address
-- :password_hash  -> Bcrypt hashed password (use bcrypt with 10 rounds)
-- :full_name      -> The superadmin's full name

INSERT INTO public.users (
    email,
    password_hash,
    full_name,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    :email,                                    -- e.g., 'admin@example.com'
    :password_hash,                            -- e.g., '$2a$10$...' (bcrypt hash)
    :full_name,                                -- e.g., 'Super Administrator'
    'superadmin',
    TRUE,
    NOW(),
    NOW()
)
RETURNING id, email, full_name, role, created_at;

-- Example with actual values (for testing only - replace password hash):
-- INSERT INTO public.users (
--     email,
--     password_hash,
--     full_name,
--     role,
--     is_active,
--     created_at,
--     updated_at
-- ) VALUES (
--     'admin@example.com',
--     '$2a$10$YourBcryptHashedPasswordHere',
--     'Super Administrator',
--     'superadmin',
--     TRUE,
--     NOW(),
--     NOW()
-- )
-- RETURNING id, email, full_name, role, created_at;

-- Note: To generate a bcrypt hash, you can:
-- 1. Use the create_superadmin.py Python script (recommended)
-- 2. Use online bcrypt generators (for testing only)
-- 3. Use bcrypt in your backend code

