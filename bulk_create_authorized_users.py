import toml
import csv
from supabase import create_client, Client
from datetime import datetime
from typing import List, Dict, Optional

def bulk_create_authorized_users(
    users: List[Dict],
    organization_id: str,
    authorized_by: Optional[str] = None,
    dry_run: bool = False
):
    """
    Bulk create authorized users for an organization
    
    Args:
        users: List of user dictionaries with keys: email, full_name, assigned_role, authorization_note
        organization_id: UUID of the organization
        authorized_by: UUID of the user authorizing these users (optional)
        dry_run: If True, only validate without creating (default: False)
    
    Returns:
        Dictionary with success/failure counts
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
    
    # Verify organization exists
    try:
        org = supabase.table('organizations').select('*').eq('id', organization_id).execute()
        if not org.data:
            print(f"❌ Error: Organization with ID {organization_id} not found")
            return {'success': 0, 'failed': len(users), 'skipped': 0}
        org_name = org.data[0].get('name', 'Unknown')
        print(f"📋 Organization: {org_name}\n")
    except Exception as e:
        print(f"❌ Error verifying organization: {e}")
        return {'success': 0, 'failed': len(users), 'skipped': 0}
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    stats = {'success': 0, 'failed': 0, 'skipped': 0}
    valid_roles = ['player', 'coach', 'admin', 'admin-team', 'admin-org']
    
    for i, user in enumerate(users, 1):
        email = user.get('email', '').strip().lower()
        full_name = user.get('full_name', '').strip()
        assigned_role = user.get('assigned_role', 'player').strip().lower()
        authorization_note = user.get('authorization_note', '').strip()
        
        print(f"[{i}/{len(users)}] Processing: {email}")
        
        # Validate
        if not email or '@' not in email:
            print(f"  ❌ Invalid email format")
            stats['failed'] += 1
            continue
        
        if assigned_role not in valid_roles:
            print(f"  ❌ Invalid role '{assigned_role}'. Must be one of: {', '.join(valid_roles)}")
            stats['failed'] += 1
            continue
        
        try:
            # Check if user already exists
            existing_user = supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                print(f"  ⏭️  Skipped - User already exists in system")
                stats['skipped'] += 1
                continue
            
            # Check if already authorized
            existing_auth = supabase.table('authorized_users').select('id').eq(
                'email', email
            ).eq('organization_id', organization_id).execute()
            
            if existing_auth.data:
                print(f"  ⏭️  Skipped - Already authorized for this organization")
                stats['skipped'] += 1
                continue
            
            if dry_run:
                print(f"  ✓ Would create: {email} as {assigned_role}")
                stats['success'] += 1
                continue
            
            # Create authorized user
            auth_data = {
                'email': email,
                'full_name': full_name if full_name else None,
                'organization_id': organization_id,
                'assigned_role': assigned_role,
                'authorized_by': authorized_by,
                'authorization_note': authorization_note if authorization_note else None,
                'is_active': True,
                'has_signed_up': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('authorized_users').insert(auth_data).execute()
            
            if result.data:
                print(f"  ✅ Created: {assigned_role}")
                stats['success'] += 1
            else:
                print(f"  ❌ Failed to create")
                stats['failed'] += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            stats['failed'] += 1
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"✅ Successfully created: {stats['success']}")
    print(f"⏭️  Skipped (already exist): {stats['skipped']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📊 Total processed: {len(users)}")
    
    return stats


def load_users_from_csv(csv_file: str) -> List[Dict]:
    """
    Load users from CSV file
    
    CSV format:
    email,full_name,assigned_role,authorization_note
    player1@team.com,John Doe,player,Starting pitcher
    coach@team.com,Jane Smith,coach,Head Coach
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        List of user dictionaries
    """
    users = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                users.append({
                    'email': row.get('email', '').strip(),
                    'full_name': row.get('full_name', '').strip(),
                    'assigned_role': row.get('assigned_role', 'player').strip(),
                    'authorization_note': row.get('authorization_note', '').strip()
                })
        
        print(f"✅ Loaded {len(users)} users from {csv_file}")
        return users
        
    except FileNotFoundError:
        print(f"❌ Error: File '{csv_file}' not found")
        return []
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []


def create_sample_csv(filename: str = "sample_users.csv"):
    """Create a sample CSV file for reference"""
    sample_data = [
        ['email', 'full_name', 'assigned_role', 'authorization_note'],
        ['player1@team.com', 'John Doe', 'player', 'Starting pitcher'],
        ['player2@team.com', 'Jane Smith', 'player', 'Center fielder'],
        ['coach@team.com', 'Bob Johnson', 'coach', 'Head Coach'],
        ['assistant@team.com', 'Mary Williams', 'coach', 'Assistant Coach'],
        ['admin@team.com', 'Tom Davis', 'admin-team', 'Team Administrator']
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    
    print(f"✅ Created sample CSV file: {filename}")


if __name__ == "__main__":
    import sys
    from create_authorized_user import list_organizations
    
    print("=== Bulk Create Authorized Users ===\n")
    
    # Check for CSV argument
    if len(sys.argv) > 1 and sys.argv[1] == '--sample':
        create_sample_csv()
        print("\nEdit the sample CSV file and run:")
        print("python bulk_create_authorized_users.py sample_users.csv")
        sys.exit(0)
    
    # Show available organizations
    print("Available Organizations:")
    orgs = list_organizations()
    
    if not orgs:
        print("No organizations found. Please create an organization first.")
        sys.exit(1)
    
    for i, org in enumerate(orgs, 1):
        print(f"{i}. {org['name']} (ID: {org['id']})")
    
    print("\n" + "="*50 + "\n")
    
    # Get organization selection
    org_choice = int(input(f"Select organization (1-{len(orgs)}): "))
    
    if org_choice < 1 or org_choice > len(orgs):
        print("Invalid organization selection")
        sys.exit(1)
    
    selected_org = orgs[org_choice - 1]
    organization_id = selected_org['id']
    
    # Get users to create
    print("\nOptions:")
    print("1. Load from CSV file")
    print("2. Enter users manually")
    
    option = input("\nSelect option (1 or 2): ")
    
    users = []
    
    if option == "1":
        csv_file = input("Enter CSV file path: ")
        users = load_users_from_csv(csv_file)
    elif option == "2":
        print("\nEnter user details (press Enter with empty email to finish):")
        while True:
            email = input("\nEmail: ").strip()
            if not email:
                break
            
            full_name = input("Full name: ").strip()
            
            print("Roles: 1=player, 2=coach, 3=admin, 4=admin-team, 5=admin-org")
            role_choice = input("Role (1-5, default=1): ").strip() or "1"
            roles = ['player', 'coach', 'admin', 'admin-team', 'admin-org']
            assigned_role = roles[int(role_choice) - 1] if role_choice.isdigit() and 1 <= int(role_choice) <= 5 else 'player'
            
            authorization_note = input("Note (optional): ").strip()
            
            users.append({
                'email': email,
                'full_name': full_name,
                'assigned_role': assigned_role,
                'authorization_note': authorization_note
            })
    else:
        print("Invalid option")
        sys.exit(1)
    
    if not users:
        print("No users to create")
        sys.exit(1)
    
    # Optional: Get authorized_by
    authorized_by = input("\nAuthorizing user ID (optional): ").strip() or None
    
    # Confirm
    print(f"\n📋 Ready to create {len(users)} users for '{selected_org['name']}'")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Cancelled")
        sys.exit(0)
    
    # Create users
    print("\n" + "="*50)
    print("CREATING USERS")
    print("="*50 + "\n")
    
    bulk_create_authorized_users(
        users=users,
        organization_id=organization_id,
        authorized_by=authorized_by,
        dry_run=False
    )

