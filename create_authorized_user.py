import toml
from supabase import create_client, Client
from datetime import datetime
from typing import Optional

def create_authorized_user(
    email: str,
    organization_id: str,
    assigned_role: str = 'player',
    full_name: Optional[str] = None,
    authorized_by: Optional[str] = None,
    authorization_note: Optional[str] = None
):
    """
    Create an authorized user who can sign up for an organization
    
    Args:
        email: Email address of the user to authorize
        organization_id: UUID of the organization
        assigned_role: Role to assign when user signs up (default: 'player')
                      Options: 'player', 'coach', 'admin', 'admin-team', 'admin-org'
        full_name: Full name of the user (optional)
        authorized_by: UUID of the user authorizing this (optional)
        authorization_note: Note about the authorization (optional)
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
    
    # Validate role
    valid_roles = ['player', 'coach', 'admin', 'admin-team', 'admin-org', 'superadmin']
    if assigned_role not in valid_roles:
        print(f"Error: Invalid role '{assigned_role}'. Must be one of: {', '.join(valid_roles)}")
        return
    
    try:
        # Check if user already exists in users table
        existing_user = supabase.table('users').select('*').eq('email', email.lower()).execute()
        if existing_user.data:
            print(f"⚠️  Warning: User with email {email} already exists in the system")
            print(f"   User ID: {existing_user.data[0]['id']}")
            print(f"   Name: {existing_user.data[0].get('full_name', 'N/A')}")
            return
        
        # Check if already authorized for this organization
        existing_auth = supabase.table('authorized_users').select('*').eq(
            'email', email.lower()
        ).eq('organization_id', organization_id).execute()
        
        if existing_auth.data:
            print(f"⚠️  Warning: User {email} is already authorized for this organization")
            print(f"   Status: {'Signed Up' if existing_auth.data[0].get('has_signed_up') else 'Pending'}")
            return
        
        # Verify organization exists
        org = supabase.table('organizations').select('*').eq('id', organization_id).execute()
        if not org.data:
            print(f"❌ Error: Organization with ID {organization_id} not found")
            return
        
        org_name = org.data[0].get('name', 'Unknown')
        
        # Insert authorized user
        auth_data = {
            'email': email.lower(),
            'full_name': full_name,
            'organization_id': organization_id,
            'assigned_role': assigned_role,
            'authorized_by': authorized_by,
            'authorization_note': authorization_note,
            'is_active': True,
            'has_signed_up': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('authorized_users').insert(auth_data).execute()
        
        if result.data:
            print(f"\n✅ Authorized user created successfully!")
            print(f"   Email: {email}")
            print(f"   Organization: {org_name}")
            print(f"   Assigned Role: {assigned_role}")
            if full_name:
                print(f"   Name: {full_name}")
            if authorization_note:
                print(f"   Note: {authorization_note}")
            print(f"   Record ID: {result.data[0]['id']}")
            print(f"\n📧 {email} can now sign up and will be automatically assigned to this organization.")
            
            return result.data[0]
        else:
            print("❌ Failed to create authorized user")
            return None
            
    except Exception as e:
        print(f"❌ Error creating authorized user: {str(e)}")
        return None


def list_organizations():
    """List all available organizations"""
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        supabase_url = secrets["connections"]["supabase"]["SUPABASE_URL"]
        supabase_key = secrets["connections"]["supabase"]["SUPABASE_KEY"]
    except:
        print("Error loading secrets.toml")
        return []
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        result = supabase.table('organizations').select('*').eq('is_active', True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching organizations: {e}")
        return []


def list_authorized_users(organization_id: Optional[str] = None):
    """List authorized users, optionally filtered by organization"""
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        supabase_url = secrets["connections"]["supabase"]["SUPABASE_URL"]
        supabase_key = secrets["connections"]["supabase"]["SUPABASE_KEY"]
    except:
        print("Error loading secrets.toml")
        return []
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        query = supabase.table('authorized_users').select('*')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        result = query.order('created_at', desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching authorized users: {e}")
        return []


if __name__ == "__main__":
    import sys
    
    print("=== Create Authorized User ===\n")
    
    # Show available organizations
    print("Available Organizations:")
    orgs = list_organizations()
    
    if not orgs:
        print("No organizations found. Please create an organization first.")
        sys.exit(1)
    
    for i, org in enumerate(orgs, 1):
        print(f"{i}. {org['name']} (ID: {org['id']})")
    
    print("\n" + "="*50 + "\n")
    
    # Get user input
    email = input("Enter user email: ")
    
    print("\nSelect organization:")
    org_choice = int(input(f"Enter number (1-{len(orgs)}): "))
    
    if org_choice < 1 or org_choice > len(orgs):
        print("Invalid organization selection")
        sys.exit(1)
    
    selected_org = orgs[org_choice - 1]
    organization_id = selected_org['id']
    
    print("\nSelect role:")
    roles = ['player', 'coach', 'admin', 'admin-team', 'admin-org']
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role}")
    
    role_choice = int(input(f"Enter number (1-{len(roles)}): "))
    
    if role_choice < 1 or role_choice > len(roles):
        print("Invalid role selection")
        sys.exit(1)
    
    assigned_role = roles[role_choice - 1]
    
    full_name = input("\nEnter full name (optional, press Enter to skip): ")
    authorization_note = input("Enter authorization note (optional, press Enter to skip): ")
    
    # Optional: Get authorized_by user ID
    authorized_by = input("\nEnter authorizing user ID (optional, press Enter to skip): ")
    
    print("\nCreating authorized user...")
    
    create_authorized_user(
        email=email,
        organization_id=organization_id,
        assigned_role=assigned_role,
        full_name=full_name if full_name else None,
        authorized_by=authorized_by if authorized_by else None,
        authorization_note=authorization_note if authorization_note else None
    )

