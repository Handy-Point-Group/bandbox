import bcrypt
import toml
from supabase import create_client, Client
from datetime import datetime

def create_superadmin(email: str, password: str, full_name: str):
    """
    Create a superadmin user with encrypted password
    
    Args:
        email: The superadmin's email address
        password: Plain text password (will be hashed)
        full_name: The superadmin's full name
    """
    
    # Load secrets from secrets.toml
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        supabase_url = secrets["connections"]["supabase"]["SUPABASE_URL"]
        supabase_key = secrets["connections"]["supabase"]["SUPABASE_KEY"]
    except FileNotFoundError:
        print("Error: secrets.toml not found at .streamlit/secrets.toml")
        return
    except KeyError as e:
        print(f"Error: Missing key in secrets.toml: {e}")
        return
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Hash the password with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=10)
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Insert the superadmin user
    try:
        result = supabase.table('users').insert({
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'role': 'superadmin',
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).execute()
        
        print(f"\n✓ Superadmin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        print(f"  User ID: {result.data[0]['id']}")
        print(f"  Role: {result.data[0]['role']}")
        
        return result.data[0]
        
    except Exception as e:
        print(f"\n✗ Error creating superadmin: {str(e)}")
        raise


if __name__ == "__main__":
    # Interactive input
    print("=== Create Superadmin User ===\n")
    
    email = input("Enter superadmin email: ")
    password = input("Enter password: ")
    full_name = input("Enter full name: ")
    
    print("\nCreating superadmin user...")
    create_superadmin(email, password, full_name)

